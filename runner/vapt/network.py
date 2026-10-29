"""Network pass — Nmap discovery/enumeration, optional Metasploit aux.

Only auxiliary/scanner Metasploit modules are used, and only when the profile
explicitly enables them. No exploit modules.
"""
from __future__ import annotations

from pathlib import Path

from .config import Config
from .ingest import ScanResult
from .targets import assert_allowed
from .util import ensure_tool, log, run, warn

DEFAULT_NMAP_ARGS = ["-sV", "-sC", "-T4", "--top-ports", "1000"]


def _nmap(cfg: Config, run_dir: Path, name: str, cidr: str,
          nmap_args: list[str]) -> ScanResult | None:
    target = assert_allowed(cidr, cfg)          # safety gate
    ensure_tool("nmap")
    out = run_dir / f"nmap-{name}.xml"
    cmd = ["nmap", *nmap_args, "-oX", str(out), target]
    proc = run(cmd, timeout=3600)
    if not out.exists():
        warn(f"nmap produced no output for {name}")
        return None
    log(f"nmap -> {out}")
    _ = proc
    return ScanResult("Nmap Scan", out, f"Network: nmap {name}")


def _metasploit_aux(cfg: Config, run_dir: Path, name: str, cidr: str) -> None:
    """Optional service verification with Metasploit auxiliary scanners."""
    try:
        ensure_tool("msfconsole")
    except Exception:
        warn("msfconsole not found; skipping Metasploit aux pass")
        return
    assert_allowed(cidr, cfg)
    rc = run_dir / f"msf-{name}.rc"
    spool = run_dir / f"msf-{name}.log"
    rc.write_text(
        f"spool {spool}\n"
        f"use auxiliary/scanner/portscan/tcp\n"
        f"set RHOSTS {cidr}\n"
        f"set THREADS 8\n"
        f"run\n"
        f"use auxiliary/scanner/http/http_version\n"
        f"set RHOSTS {cidr}\n"
        f"run\n"
        f"spool off\n"
        f"exit\n",
        encoding="utf-8",
    )
    run(["msfconsole", "-q", "-r", str(rc)], timeout=3600)
    log(f"metasploit aux log -> {spool}")


def run_pass(cfg: Config, run_dir: Path, pconf: dict) -> list[ScanResult]:
    results: list[ScanResult] = []
    nmap_args = pconf.get("nmap_args", DEFAULT_NMAP_ARGS)
    use_msf = bool(pconf.get("metasploit", False))

    nets = cfg.targets.get("network", [])
    if not nets:
        warn("no network targets configured (targets.network)")
    for t in nets:
        name, cidr = t["name"], t["cidr"]
        log(f"network pass: {name} ({cidr})")
        res = _nmap(cfg, run_dir, name, cidr, nmap_args)
        if res:
            results.append(res)
        if use_msf:
            _metasploit_aux(cfg, run_dir, name, cidr)
    return results
