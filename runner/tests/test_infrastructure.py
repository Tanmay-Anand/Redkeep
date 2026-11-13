"""The lab network's infrastructure is never a target, and a slow tool never ends a run.

The Docker gateway on the lab network is the host machine: it forwards every port the
host publishes (a developer's own databases, for example). A sweep of the lab CIDR once
fingerprinted those, so these tests pin the exclusion behaviour. Everything is offline:
infrastructure discovery is monkeypatched and the routing table is a temp file.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from vapt import network, targets, util
from vapt.config import Config
from vapt.targets import TargetNotAllowed, assert_allowed, network_exclusions


def make_cfg(hosts=None) -> Config:
    return Config(
        {"lab": {"allowed_hosts": hosts or [], "allowed_cidrs": ["172.30.0.0/24"]}},
        Path("test-config.yaml"),
    )


@pytest.fixture(autouse=True)
def fixed_infrastructure(monkeypatch):
    """Pretend we run in the toolbox at 172.30.0.3 behind gateway 172.30.0.1."""
    monkeypatch.setattr(targets, "infrastructure_ips",
                        lambda: frozenset({"172.30.0.1", "172.30.0.3", "192.168.65.254"}))


# --- routing table parsing -------------------------------------------------
def test_default_gateway_read_from_route_table(tmp_path):
    rt = tmp_path / "route"
    rt.write_text(
        "Iface\tDestination\tGateway\tFlags\tRefCnt\tUse\tMetric\tMask\n"
        "eth0\t00000000\t01001EAC\t0003\t0\t0\t0\t00000000\n"     # default via 172.30.0.1
        "eth0\t00001EAC\t00000000\t0001\t0\t0\t0\t00FFFFFF\n",
        encoding="ascii")
    assert targets._default_gateway(rt) == "172.30.0.1"


def test_default_gateway_missing_table_is_none(tmp_path):
    assert targets._default_gateway(tmp_path / "nope") is None


# --- sweep exclusions --------------------------------------------------------
def test_sweep_excludes_gateway_and_toolbox_only_inside_range():
    # 192.168.65.254 (host alias) is outside the /24, so it isn't listed.
    assert network_exclusions("172.30.0.0/24") == ["172.30.0.1", "172.30.0.3"]


def test_sweep_excludes_first_host_even_without_route_info(monkeypatch):
    monkeypatch.setattr(targets, "infrastructure_ips", lambda: frozenset())
    assert network_exclusions("10.9.0.0/24") == ["10.9.0.1"]


def test_sweep_adds_configured_extras_and_ignores_junk():
    got = network_exclusions("172.30.0.0/24", ["172.30.0.250", "not-an-ip", "10.0.0.9"])
    assert got == ["172.30.0.1", "172.30.0.3", "172.30.0.250"]


# --- single-host targets -----------------------------------------------------
@pytest.mark.parametrize("target", ["172.30.0.1", "http://172.30.0.1:8080", "172.30.0.3:5432"])
def test_gateway_or_toolbox_as_target_is_refused(target):
    with pytest.raises(TargetNotAllowed):
        assert_allowed(target, make_cfg())


def test_name_resolving_to_gateway_is_refused(monkeypatch):
    monkeypatch.setattr(targets.socket, "gethostbyname", lambda _h: "172.30.0.1")
    with pytest.raises(TargetNotAllowed):
        assert_allowed("http://sneaky-name:5432", make_cfg())


def test_ordinary_lab_host_still_allowed():
    assert assert_allowed("172.30.0.2", make_cfg()) == "172.30.0.2"


def test_allowlisted_lab_service_name_still_allowed():
    assert assert_allowed("http://target-api:3000", make_cfg(["target-api"])) == "target-api"


def test_cidr_sweep_itself_still_allowed():
    # The sweep is allowed; the infrastructure inside it is excluded by the pass.
    assert assert_allowed("172.30.0.0/24", make_cfg()) == "172.30.0.0/24"


# --- the network pass wires it through ---------------------------------------
def test_nmap_gets_exclude_and_host_timeout(monkeypatch, tmp_path):
    seen = {}

    def fake_run(cmd, **kw):
        seen["cmd"], seen["timeout"] = cmd, kw.get("timeout")
        (tmp_path / "nmap-lab.xml").write_text("<nmaprun/>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(network, "run", fake_run)
    monkeypatch.setattr(network, "ensure_tool", lambda _n: "/usr/bin/nmap")
    cfg = Config({"lab": {"allowed_cidrs": ["172.30.0.0/24"]},
                  "targets": {"network": [{"name": "lab", "cidr": "172.30.0.0/24"}]}},
                 Path("test-config.yaml"))
    network.run_pass(cfg, tmp_path, {"nmap_args": ["-sV"], "host_timeout": "5m",
                                     "timeout": 120})
    cmd = seen["cmd"]
    assert cmd[cmd.index("--exclude") + 1] == "172.30.0.1,172.30.0.3"
    assert cmd[cmd.index("--host-timeout") + 1] == "5m"
    assert cmd[-1] == "172.30.0.0/24" and seen["timeout"] == 120


def test_live_hosts_drops_excluded(tmp_path):
    xml = tmp_path / "n.xml"
    xml.write_text(
        "<nmaprun>"
        "<host><status state='up'/><address addr='172.30.0.1' addrtype='ipv4'/></host>"
        "<host><status state='up'/><address addr='172.30.0.2' addrtype='ipv4'/></host>"
        "<host><status state='down'/><address addr='172.30.0.9' addrtype='ipv4'/></host>"
        "</nmaprun>", encoding="utf-8")
    assert network._live_hosts(xml, ["172.30.0.1"]) == ["172.30.0.2"]
    assert network._live_hosts(tmp_path / "missing.xml", []) == []


# --- timeouts no longer crash the run ----------------------------------------
def test_run_timeout_returns_124_instead_of_raising():
    proc = util.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=1)
    assert proc.returncode == util.TIMEOUT_RC


def test_run_timeout_with_check_raises_called_process_error():
    with pytest.raises(subprocess.CalledProcessError):
        util.run([sys.executable, "-c", "import time; time.sleep(5)"], timeout=1, check=True)
