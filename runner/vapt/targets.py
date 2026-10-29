"""Target allowlist gate — the core safety control.

Nothing in Redkeep may scan a target that is not on the configured lab network.
Every pass calls :func:`assert_allowed` (directly or via :func:`require_url`)
before launching a tool. A target is allowed only if:

  * its hostname is explicitly listed in ``lab.allowed_hosts``, OR
  * it resolves to an IP address inside one of ``lab.allowed_cidrs``.

Anything else raises :class:`TargetNotAllowed` and the pass aborts before a
single packet is sent.
"""
from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from .config import Config


class TargetNotAllowed(RuntimeError):
    """Raised when a target is outside the authorised lab network."""


def _host_of(target: str) -> str:
    """Extract a bare host from a URL, host:port, or CIDR/host string."""
    t = target.strip()
    if "://" in t:
        return urlparse(t).hostname or ""
    # strip any :port
    if "/" in t:            # a CIDR like 172.30.0.0/24
        return t
    return t.split(":")[0]


def _in_allowed_cidr(ip: str, cidrs: list[str]) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    for c in cidrs:
        try:
            if addr in ipaddress.ip_network(c, strict=False):
                return True
        except ValueError:
            continue
    return False


def _cidr_within(cidr: str, allowed: list[str]) -> bool:
    try:
        net = ipaddress.ip_network(cidr, strict=False)
    except ValueError:
        return False
    for c in allowed:
        try:
            allowed_net = ipaddress.ip_network(c, strict=False)
        except ValueError:
            continue
        # subnet_of raises TypeError across IP versions, so compare same-version
        # networks only (and this keeps the types concrete for the checker).
        if isinstance(net, ipaddress.IPv4Network) and isinstance(
            allowed_net, ipaddress.IPv4Network
        ):
            if net.subnet_of(allowed_net):
                return True
        elif isinstance(net, ipaddress.IPv6Network) and isinstance(
            allowed_net, ipaddress.IPv6Network
        ):
            if net.subnet_of(allowed_net):
                return True
    return False


def assert_allowed(target: str, cfg: Config) -> str:
    """Return the validated host/target, or raise :class:`TargetNotAllowed`.

    Accepts a URL, host, host:port, or CIDR. CIDRs are allowed only if fully
    contained in an allowed CIDR.
    """
    host = _host_of(target)
    if not host:
        raise TargetNotAllowed(f"could not parse a host from target: {target!r}")

    # A CIDR target (e.g. network sweep) must sit within an allowed CIDR.
    if "/" in host:
        if _cidr_within(host, cfg.allowed_cidrs):
            return host
        raise TargetNotAllowed(
            f"CIDR {host!r} is not within any lab.allowed_cidrs {cfg.allowed_cidrs}"
        )

    # Explicitly allowlisted hostname (lab service names resolve only in-lab).
    if host in cfg.allowed_hosts:
        return host

    # Otherwise it must resolve into an allowed CIDR.
    try:
        ip = socket.gethostbyname(host)
    except OSError:
        raise TargetNotAllowed(
            f"host {host!r} is not in lab.allowed_hosts and could not be "
            "resolved to an allowed IP. Refusing (safety gate)."
        ) from None
    if _in_allowed_cidr(ip, cfg.allowed_cidrs):
        return host

    raise TargetNotAllowed(
        f"host {host!r} resolves to {ip}, which is outside lab.allowed_cidrs "
        f"{cfg.allowed_cidrs}. Refusing (safety gate)."
    )


def require_url(url: str, cfg: Config) -> str:
    """Validate a URL target and return it unchanged if allowed."""
    assert_allowed(url, cfg)
    return url
