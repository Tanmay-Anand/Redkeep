"""Tests for the target allowlist gate — Redkeep's core safety control.

A regression here could let a scan reach a host outside the lab (e.g. prod), so
this is the most important thing to keep green. The tests never touch the real
network: they use allowlisted names, pure CIDR math, and IP literals (which
``gethostbyname`` resolves to themselves offline), and monkeypatch DNS for the
resolve-into-CIDR branch so results are deterministic in CI.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from vapt.config import Config
from vapt.targets import TargetNotAllowed, assert_allowed, require_url


def make_cfg(hosts=None, cidrs=None) -> Config:
    return Config(
        {
            "lab": {
                "allowed_hosts": ["target-api"] if hosts is None else hosts,
                "allowed_cidrs": ["172.30.0.0/24"] if cidrs is None else cidrs,
            }
        },
        Path("test-config.yaml"),
    )


# --- allowlisted hostnames (URL / host / host:port) ------------------------
@pytest.mark.parametrize(
    "target",
    [
        "target-api",
        "http://target-api:8080",
        "http://target-api:3000/some/path",
        "target-api:8080",
    ],
)
def test_allowlisted_host_allowed(target):
    assert assert_allowed(target, make_cfg()) == "target-api"


def test_host_not_allowlisted_and_outside_cidr_refused():
    # 8.8.8.8 is an IP literal (resolves to itself offline), outside the lab CIDR.
    with pytest.raises(TargetNotAllowed):
        assert_allowed("8.8.8.8", make_cfg())


# --- IP literals vs CIDR (fully offline) -----------------------------------
def test_ip_literal_inside_cidr_allowed():
    assert assert_allowed("172.30.0.5", make_cfg(hosts=[])) == "172.30.0.5"


def test_ip_literal_outside_cidr_refused():
    with pytest.raises(TargetNotAllowed):
        assert_allowed("10.0.0.5", make_cfg(hosts=[]))


# --- CIDR targets (network sweep) ------------------------------------------
def test_cidr_equal_to_allowed_passes():
    assert assert_allowed("172.30.0.0/24", make_cfg()) == "172.30.0.0/24"


def test_cidr_subnet_of_allowed_passes():
    cfg = make_cfg(cidrs=["172.30.0.0/16"])
    assert assert_allowed("172.30.0.0/24", cfg) == "172.30.0.0/24"


def test_cidr_wider_than_allowed_refused():
    # A /16 is NOT contained in a /24 — must be refused.
    with pytest.raises(TargetNotAllowed):
        assert_allowed("172.30.0.0/16", make_cfg(cidrs=["172.30.0.0/24"]))


def test_cidr_different_range_refused():
    with pytest.raises(TargetNotAllowed):
        assert_allowed("10.0.0.0/8", make_cfg())


# --- DNS resolution branch (monkeypatched, deterministic) ------------------
def test_host_resolving_into_cidr_allowed(monkeypatch):
    monkeypatch.setattr("vapt.targets.socket.gethostbyname", lambda h: "172.30.0.9")
    assert assert_allowed("some-lab-host", make_cfg(hosts=[])) == "some-lab-host"


def test_host_resolving_outside_cidr_refused(monkeypatch):
    monkeypatch.setattr("vapt.targets.socket.gethostbyname", lambda h: "93.184.216.34")
    with pytest.raises(TargetNotAllowed):
        assert_allowed("example.com", make_cfg(hosts=[]))


def test_host_unresolvable_refused(monkeypatch):
    def boom(_h):
        raise OSError("name or service not known")

    monkeypatch.setattr("vapt.targets.socket.gethostbyname", boom)
    with pytest.raises(TargetNotAllowed):
        assert_allowed("nope.invalid", make_cfg(hosts=[]))


# --- parsing edge cases ----------------------------------------------------
def test_unparseable_target_refused():
    with pytest.raises(TargetNotAllowed):
        assert_allowed("://", make_cfg())


def test_empty_cidrs_refuses_cidr_target():
    with pytest.raises(TargetNotAllowed):
        assert_allowed("172.30.0.0/24", make_cfg(cidrs=[]))


# --- require_url wrapper ---------------------------------------------------
def test_require_url_returns_unchanged_when_allowed():
    url = "http://target-api:8080/health"
    assert require_url(url, make_cfg()) == url


def test_require_url_raises_when_not_allowed():
    with pytest.raises(TargetNotAllowed):
        require_url("http://8.8.8.8/", make_cfg())
