"""Offline reporting.

Parses the raw tool output in a run directory into a consolidated set of
findings and renders a standalone HTML report with Jinja2. Works with only the
lab up — DefectDojo is not required. When DefectDojo IS used, it remains the
live triage UI; this report is the shareable, point-in-time artefact.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import Config
from .util import log, warn

SEVERITY_ORDER = ["Critical", "High", "Medium", "Low", "Info"]
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "reports" / "templates"


@dataclass
class Finding:
    tool: str
    name: str
    severity: str
    count: int = 1
    detail: str = ""
    reference: str = ""


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def add(self, f: Finding) -> None:
        self.findings.append(f)

    def summary(self) -> dict[str, int]:
        out = {s: 0 for s in SEVERITY_ORDER}
        for f in self.findings:
            out[f.severity] = out.get(f.severity, 0) + f.count
        return out


# --- parsers -------------------------------------------------------------------

_ZAP_RISK = {"0": "Info", "1": "Low", "2": "Medium", "3": "High"}


def _text(el, tag, default="") -> str:
    child = el.find(tag)
    return (child.text or default).strip() if child is not None and child.text else default


def _parse_nmap(path: Path, rep: Report) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return
    for host in root.findall("host"):
        addr = ""
        a = host.find("address")
        if a is not None:
            addr = a.get("addr", "")
        for port in host.findall("./ports/port"):
            state = port.find("state")
            if state is None or state.get("state") != "open":
                continue
            svc = port.find("service")
            sname = svc.get("name", "?") if svc is not None else "?"
            sver = (svc.get("product", "") + " " + svc.get("version", "")).strip() if svc is not None else ""
            rep.add(Finding(
                tool="nmap", severity="Info",
                name=f"Open port {port.get('portid')}/{port.get('protocol')} ({sname})",
                detail=f"{addr}: {sname} {sver}".strip(),
            ))


def _parse_zap(path: Path, rep: Report) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return
    for item in root.iter("alertitem"):
        name = _text(item, "name") or _text(item, "alert")
        risk = _ZAP_RISK.get(_text(item, "riskcode", "0"), "Info")
        try:
            count = int(_text(item, "count", "1") or "1")
        except ValueError:
            count = 1
        cwe = _text(item, "cweid")
        wasc = _text(item, "wascid")
        ref = " ".join(x for x in [f"CWE-{cwe}" if cwe else "", f"WASC-{wasc}" if wasc else ""] if x)
        rep.add(Finding(tool="zap", severity=risk, name=name or "ZAP alert",
                        count=count, reference=ref))


def _parse_nuclei(path: Path, rep: Report) -> None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        info = obj.get("info", {})
        sev = (info.get("severity", "info") or "info").capitalize()
        if sev == "Critical":
            sev = "Critical"
        elif sev not in SEVERITY_ORDER:
            sev = "Info"
        rep.add(Finding(
            tool="nuclei", severity=sev,
            name=info.get("name", obj.get("template-id", "nuclei finding")),
            detail=obj.get("matched-at", ""),
            reference=obj.get("template-id", ""),
        ))


def _parse_nikto(path: Path, rep: Report) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return
    for item in root.iter("item"):
        desc = _text(item, "description") or item.get("id", "nikto item")
        rep.add(Finding(tool="nikto", severity="Medium", name=desc[:120]))


def _parse_junit(path: Path, rep: Report, tool: str) -> None:
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return
    for case in root.iter("testcase"):
        failure = case.find("failure")
        error = case.find("error")
        node = failure if failure is not None else error
        if node is None:
            continue
        name = case.get("name", "test")
        msg = (node.get("message") or "").strip()
        rep.add(Finding(tool=tool, severity="Medium",
                        name=f"{name}", detail=msg[:300]))


# --- build ---------------------------------------------------------------------

def _latest_run_dir(cfg: Config) -> Path | None:
    base = Path(cfg.data.get("output_dir", "reports/output"))
    if not base.exists():
        return None
    dirs = sorted((d for d in base.iterdir() if d.is_dir()), reverse=True)
    return dirs[0] if dirs else None


def build_offline(cfg: Config, run_dir: Path | None = None) -> Path | None:
    run_dir = run_dir or _latest_run_dir(cfg)
    if not run_dir or not run_dir.exists():
        warn("no run directory found to report on (run a scan first)")
        return None

    rep = Report()
    for f in sorted(run_dir.iterdir()):
        n = f.name
        if n.startswith("nmap-") and n.endswith(".xml"):
            _parse_nmap(f, rep)
        elif n.startswith("zap-") and n.endswith(".xml"):
            _parse_zap(f, rep)
        elif n.startswith("nuclei-") and n.endswith(".jsonl"):
            _parse_nuclei(f, rep)
        elif n.startswith("nikto-") and n.endswith(".xml"):
            _parse_nikto(f, rep)
        elif n.startswith("schemathesis-") and n.endswith(".xml"):
            _parse_junit(f, rep, "schemathesis")
        elif n.startswith("newman-") and n.endswith(".xml"):
            _parse_junit(f, rep, "newman")

    rep.findings.sort(key=lambda x: SEVERITY_ORDER.index(x.severity)
                      if x.severity in SEVERITY_ORDER else len(SEVERITY_ORDER))

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    tpl = env.get_template("report.html.j2")
    html = tpl.render(
        product=cfg.defectdojo.get("product_name", "target"),
        engagement=cfg.defectdojo.get("engagement_name", "engagement"),
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        run_dir=str(run_dir),
        summary=rep.summary(),
        findings=rep.findings,
        severity_order=SEVERITY_ORDER,
    )
    out = run_dir / "report.html"
    out.write_text(html, encoding="utf-8")
    log(f"offline report -> {out}  ({len(rep.findings)} finding rows)")
    return out
