"""API-security pass — schemathesis (spec fuzzing), ZAP API scan, optional Newman.

schemathesis drives property/fuzz tests straight from each service's OpenAPI
spec. ZAP imports the same spec and active-scans it. Both can run authenticated
using the headers produced by ``vapt.auth`` (confirmed from the CRM at Phase 4).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from . import auth
from .config import Config
from .ingest import ScanResult
from .targets import require_url
from .util import ensure_tool, log, run, warn


def _zap_bin() -> str:
    for name in ("zap.sh", "zaproxy", "zap"):
        if shutil.which(name):
            return name
    raise FileNotFoundError("OWASP ZAP not found (zap.sh/zaproxy).")


def _schemathesis(cfg: Config, run_dir: Path, name: str, spec: str,
                  base_url: str) -> ScanResult | None:
    require_url(base_url, cfg)                   # safety gate
    try:
        ensure_tool("schemathesis")
    except Exception:
        warn("schemathesis not found; skipping")
        return None
    junit = run_dir / f"schemathesis-{name}.xml"
    cmd = [
        "schemathesis", "run", spec,
        "--base-url", base_url,
        "--checks", "all",
        "--hypothesis-max-examples", str(cfg.data.get("schemathesis_examples", 50)),
        "--junit-xml", str(junit),
    ]
    cmd += auth.header_args(cfg)
    run(cmd, timeout=5400)
    if not junit.exists():
        warn(f"schemathesis produced no report for {name}")
        return None
    log(f"schemathesis -> {junit}")
    # DefectDojo ingests JUnit test failures as findings.
    return ScanResult("JUnit Test Report", junit, f"API: schemathesis {name}")


def _zap_api(cfg: Config, run_dir: Path, name: str, spec: str,
             base_url: str) -> ScanResult | None:
    require_url(base_url, cfg)
    zap = _zap_bin()
    report_file = f"zap-api-{name}.xml"
    plan = run_dir / f"zap-api-{name}-plan.yaml"
    plan.write_text(
        "env:\n"
        "  contexts:\n"
        "    - name: ctx\n"
        "      urls:\n"
        f"        - {base_url}\n"
        "  parameters:\n"
        "    failOnError: false\n"
        "jobs:\n"
        "  - type: openapi\n"
        "    parameters:\n"
        f"      apiUrl: {spec}\n"
        f"      targetUrl: {base_url}\n"
        "      context: ctx\n"
        "  - type: passiveScan-wait\n"
        "  - type: activeScan\n"
        "    parameters:\n"
        "      context: ctx\n"
        "      maxRuleDurationInMins: 2\n"
        "  - type: report\n"
        "    parameters:\n"
        "      template: traditional-xml\n"
        # Absolute: ZAP resolves plan-relative paths against the plan dir.
        f"      reportDir: {run_dir.resolve()}\n"
        f"      reportFile: {report_file}\n",
        encoding="utf-8",
    )
    # zap.sh cd's to its install dir, so the plan path must be absolute too.
    run([zap, "-cmd", "-autorun", str(plan.resolve())], timeout=5400)
    out = run_dir / report_file
    if not out.exists():
        warn(f"ZAP API scan produced no report for {name}")
        return None
    log(f"ZAP API -> {out}")
    return ScanResult("ZAP Scan", out, f"API: ZAP {name}")


def _newman(cfg: Config, run_dir: Path, name: str, collection: str,
            base_url: str) -> ScanResult | None:
    require_url(base_url, cfg)
    try:
        ensure_tool("newman")
    except Exception:
        warn("newman not found; skipping")
        return None
    junit = run_dir / f"newman-{name}.xml"
    run(["newman", "run", collection,
         "--env-var", f"baseUrl={base_url}",
         "--reporters", "cli,junit",
         "--reporter-junit-export", str(junit)], timeout=1800)
    if not junit.exists():
        return None
    log(f"newman -> {junit}")
    return ScanResult("JUnit Test Report", junit, f"API: newman {name}")


def run_pass(cfg: Config, run_dir: Path, pconf: dict) -> list[ScanResult]:
    results: list[ScanResult] = []
    do_schemathesis = pconf.get("schemathesis", True)
    do_zap = pconf.get("zap_api", True)

    apis = cfg.targets.get("api", [])
    if not apis:
        warn("no api targets configured (targets.api)")
    for t in apis:
        name = t["name"]
        base_url = t["base_url"]
        spec = t.get("openapi")
        log(f"api pass: {name} ({base_url})")
        if not spec:
            warn(f"{name}: no openapi spec configured; skipping schemathesis/ZAP-API")
        else:
            if do_schemathesis:
                res = _schemathesis(cfg, run_dir, name, spec, base_url)
                if res:
                    results.append(res)
            if do_zap:
                res = _zap_api(cfg, run_dir, name, spec, base_url)
                if res:
                    results.append(res)
        if t.get("postman"):
            res = _newman(cfg, run_dir, name, t["postman"], base_url)
            if res:
                results.append(res)
    return results
