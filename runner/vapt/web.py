"""Web-application pass — OWASP ZAP, nuclei, nikto.

ZAP is driven through its built-in Automation Framework (``zap.sh -cmd
-autorun plan.yaml``) using only core jobs (spider, passive scan, optional
active scan, XML report) so no paid tooling or extra add-ons are required.
Burp Community is not used here — it cannot be scripted; drive it by hand from
the toolbox for manual deep-dives.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from .config import Config
from .ingest import ScanResult
from .targets import require_url
from .util import ensure_tool, log, run, warn


def _zap_bin() -> str:
    for name in ("zap.sh", "zaproxy", "zap"):
        if shutil.which(name):
            return name
    raise FileNotFoundError(
        "OWASP ZAP not found (zap.sh/zaproxy). Run inside the Kali toolbox."
    )


def _zap_plan(url: str, report_dir: Path, report_file: str, active: bool) -> str:
    jobs = [
        "  - type: spider\n"
        "    parameters:\n"
        "      context: ctx\n"
        f"      url: {url}\n"
        "      maxDuration: 5\n",
        "  - type: passiveScan-wait\n"
        "    parameters:\n"
        "      maxDuration: 5\n",
    ]
    if active:
        jobs.append(
            "  - type: activeScan\n"
            "    parameters:\n"
            "      context: ctx\n"
            "      maxRuleDurationInMins: 2\n"
        )
    jobs.append(
        "  - type: report\n"
        "    parameters:\n"
        "      template: traditional-xml\n"
        f"      reportDir: {report_dir}\n"
        f"      reportFile: {report_file}\n"
    )
    return (
        "env:\n"
        "  contexts:\n"
        "    - name: ctx\n"
        "      urls:\n"
        f"        - {url}\n"
        "  parameters:\n"
        "    failOnError: false\n"
        "    progressToStdout: true\n"
        "jobs:\n" + "".join(jobs)
    )


def _zap(cfg: Config, run_dir: Path, name: str, url: str, active: bool) -> ScanResult | None:
    require_url(url, cfg)                        # safety gate
    zap = _zap_bin()
    report_file = f"zap-{name}.xml"
    plan = run_dir / f"zap-{name}-plan.yaml"
    # ZAP's Automation Framework resolves plan-relative paths against the plan
    # file's own directory, so a relative reportDir gets doubled. Pass absolute.
    plan.write_text(_zap_plan(url, run_dir.resolve(), report_file, active), encoding="utf-8")
    # zap.sh cd's to its install dir, so the plan path must be absolute too.
    run([zap, "-cmd", "-autorun", str(plan.resolve())], timeout=5400)
    out = run_dir / report_file
    if not out.exists():
        warn(f"ZAP produced no report for {name}")
        return None
    log(f"ZAP -> {out}")
    return ScanResult("ZAP Scan", out, f"Web: ZAP {name} ({'active' if active else 'baseline'})")


def _nuclei(cfg: Config, run_dir: Path, name: str, url: str) -> ScanResult | None:
    require_url(url, cfg)
    try:
        ensure_tool("nuclei")
    except Exception:
        warn("nuclei not found; skipping")
        return None
    out = run_dir / f"nuclei-{name}.jsonl"
    run(["nuclei", "-u", url, "-jsonl", "-o", str(out), "-silent"], timeout=3600)
    if not out.exists() or out.stat().st_size == 0:
        warn(f"nuclei produced no findings for {name}")
        return None
    log(f"nuclei -> {out}")
    return ScanResult("Nuclei Scan", out, f"Web: nuclei {name}")


def _nikto(cfg: Config, run_dir: Path, name: str, url: str) -> ScanResult | None:
    require_url(url, cfg)
    try:
        ensure_tool("nikto")
    except Exception:
        warn("nikto not found; skipping")
        return None
    out = run_dir / f"nikto-{name}.xml"
    run(["nikto", "-h", url, "-Format", "xml", "-output", str(out)], timeout=3600)
    if not out.exists():
        warn(f"nikto produced no output for {name}")
        return None
    log(f"nikto -> {out}")
    return ScanResult("Nikto Scan", out, f"Web: nikto {name}")


def run_pass(cfg: Config, run_dir: Path, pconf: dict) -> list[ScanResult]:
    results: list[ScanResult] = []
    zap_mode = (pconf.get("zap") or {}).get("mode", "baseline")  # baseline | full | off
    do_nuclei = pconf.get("nuclei", True)
    do_nikto = pconf.get("nikto", True)

    webs = cfg.targets.get("web", [])
    if not webs:
        warn("no web targets configured (targets.web)")
    for t in webs:
        name, url = t["name"], t["url"]
        log(f"web pass: {name} ({url})")
        if zap_mode in ("baseline", "full"):
            res = _zap(cfg, run_dir, name, url, active=(zap_mode == "full"))
            if res:
                results.append(res)
        if do_nuclei:
            res = _nuclei(cfg, run_dir, name, url)
            if res:
                results.append(res)
        if do_nikto:
            res = _nikto(cfg, run_dir, name, url)
            if res:
                results.append(res)
    return results
