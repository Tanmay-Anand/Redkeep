"""Network pass — Nmap discovery/enumeration, optional Metasploit aux.

Only auxiliary/scanner Metasploit modules are used, and only when the profile
explicitly enables them. No exploit modules.

Sweeps never touch the lab network's infrastructure: the Docker gateway (the host
machine, which forwards every port the host publishes) and this toolbox container are
excluded from nmap, and Metasploit only gets the live lab hosts nmap found.
"""
from __future__ import annotations

from pathlib import Path

from defusedxml.ElementTree import parse as _xml_parse

from .config import Config
from .ingest import ScanResult
from .targets import assert_allowed, network_exclusions
from .util import ensure_tool, log, run, warn

DEFAULT_NMAP_ARGS = ["-sV", "-sC", "-T4", "--top-ports", "1000"]
# nmap gives up on a single host after this long, so one slow host can't eat the pass
# (and nmap still writes complete XML for the rest). Profile key: network.host_timeout.
DEFAULT_HOST_TIMEOUT = "15m"
# Wall-clock limit for one tool run. Profile key: network.timeout (seconds).
DEFAULT_TOOL_TIMEOUT = 3600


def _nmap(cfg: Config, run_dir: Path, name: str, cidr: str, nmap_args: list[str],
          exclude: list[str], host_timeout: str, timeout: int) -> ScanResult | None:
    target = assert_allowed(cidr, cfg)          # safety gate
    ensure_tool("nmap")
    out = run_dir / f"nmap-{name}.xml"
    args = list(nmap_args)
    if host_timeout and "--host-timeout" not in args:
        args += ["--host-timeout", host_timeout]
    if exclude:
        args += ["--exclude", ",".join(exclude)]
    cmd = ["nmap", *args, "-oX", str(out), target]
    run(cmd, timeout=timeout)
    if not out.exists():
        warn(f"nmap produced no output for {name}")
        return None
    log(f"nmap -> {out}")
    return ScanResult("Nmap Scan", out, f"Network: nmap {name}")


def _live_hosts(xml_path: Path, exclude: list[str]) -> list[str]:
    """Up hosts from an nmap XML file, minus exclusions ([] if missing/unparseable)."""
    try:
        root = _xml_parse(xml_path).getroot()
    except Exception:
        return []
    hosts = []
    for h in root.findall("host"):
        st = h.find("status")
        a = h.find("address[@addrtype='ipv4']")
        if st is not None and st.get("state") == "up" and a is not None:
            ip = a.get("addr", "")
            if ip and ip not in exclude:
                hosts.append(ip)
    return hosts


def _metasploit_aux(cfg: Config, run_dir: Path, name: str, hosts: list[str],
                    timeout: int) -> None:
    """Optional service verification with Metasploit auxiliary scanners."""
    try:
        ensure_tool("msfconsole")
    except Exception:
        warn("msfconsole not found; skipping Metasploit aux pass")
        return
    if not hosts:
        warn(f"no live lab hosts from nmap for {name}; skipping Metasploit aux pass")
        return
    for h in hosts:
        assert_allowed(h, cfg)                  # safety gate, per host
    rhosts = " ".join(hosts)
    rc = run_dir / f"msf-{name}.rc"
    spool = run_dir / f"msf-{name}.log"
    rc.write_text(
        f"spool {spool}\n"
        f"use auxiliary/scanner/portscan/tcp\n"
        f"set RHOSTS {rhosts}\n"
        f"set THREADS 8\n"
        f"run\n"
        f"use auxiliary/scanner/http/http_version\n"
        f"set RHOSTS {rhosts}\n"
        f"run\n"
        f"spool off\n"
        f"exit\n",
        encoding="utf-8",
    )
    run(["msfconsole", "-q", "-r", str(rc)], timeout=timeout)
    log(f"metasploit aux log -> {spool}")


def run_pass(cfg: Config, run_dir: Path, pconf: dict) -> list[ScanResult]:
    results: list[ScanResult] = []
    nmap_args = pconf.get("nmap_args", DEFAULT_NMAP_ARGS)
    use_msf = bool(pconf.get("metasploit", False))
    host_timeout = str(pconf.get("host_timeout", DEFAULT_HOST_TIMEOUT))
    timeout = int(pconf.get("timeout", DEFAULT_TOOL_TIMEOUT))

    nets = cfg.targets.get("network", [])
    if not nets:
        warn("no network targets configured (targets.network)")
    for t in nets:
        name, cidr = t["name"], t["cidr"]
        exclude = network_exclusions(cidr, t.get("exclude", []) or [])
        log(f"network pass: {name} ({cidr})")
        if exclude:
            log(f"  excluding {', '.join(exclude)} (lab gateway = host machine, "
                "this toolbox, or configured)")
        res = _nmap(cfg, run_dir, name, cidr, nmap_args, exclude, host_timeout, timeout)
        if res:
            results.append(res)
        if use_msf:
            _metasploit_aux(cfg, run_dir, name,
                            _live_hosts(run_dir / f"nmap-{name}.xml", exclude), timeout)
    return results
