"""Target allowlist gate — the core safety control.

Nothing in Redkeep may scan a target that is not on the configured lab network.
Every pass calls :func:`assert_allowed` (directly or via :func:`require_url`)
before launching a tool. A target is allowed only if:

  * its hostname is explicitly listed in ``lab.allowed_hosts``, OR
  * it resolves to an IP address inside one of ``lab.allowed_cidrs``.

Anything else raises :class:`TargetNotAllowed` and the pass aborts before a
single packet is sent.

Being inside an allowed CIDR is not enough on its own: the lab network also holds
**infrastructure** that is not a lab target — the Docker gateway (the host machine,
which forwards every port the host publishes, e.g. a developer's own databases) and
the toolbox container itself. Single-host targets that are infrastructure are
refused, and network sweeps exclude them (see :func:`network_exclusions`).
"""
from __future__ import annotations

import functools
import ipaddress
import socket
from collections.abc import Iterable
from pathlib import Path
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


# --- infrastructure on the lab network ------------------------------------------
_ROUTE_TABLE = Path("/proc/net/route")
# Names Docker Desktop / Docker Engine give the host machine inside containers.
_HOST_ALIASES = ("host.docker.internal", "gateway.docker.internal")


def _default_gateway(route_table: Path = _ROUTE_TABLE) -> str | None:
    """IPv4 default gateway from the Linux routing table, or None if unavailable."""
    try:
        lines = route_table.read_text(encoding="ascii").splitlines()[1:]
    except OSError:
        return None
    for line in lines:
        f = line.split()
        if len(f) > 2 and f[1] == "00000000" and f[2] != "00000000":   # destination 0.0.0.0
            return str(ipaddress.IPv4Address(bytes.fromhex(f[2])[::-1]))  # little-endian hex
    return None


def _own_ipv4s() -> set[str]:
    try:
        infos = socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET)
    except OSError:
        return set()
    return {str(i[4][0]) for i in infos} - {"127.0.0.1"}


@functools.lru_cache(maxsize=1)
def infrastructure_ips() -> frozenset[str]:
    """Addresses that must never be scanned as lab targets.

    The Docker gateway (from the routing table), the host-machine aliases Docker
    provides, and this container's own addresses. Cached: they don't change mid-run.
    """
    ips: set[str] = set(_own_ipv4s())
    gw = _default_gateway()
    if gw:
        ips.add(gw)
    for name in _HOST_ALIASES:
        try:
            ips.add(socket.gethostbyname(name))
        except OSError:
            continue
    return frozenset(ips)


def _first_host(net: ipaddress.IPv4Network | ipaddress.IPv6Network) -> str | None:
    """Docker gives a bridge network's gateway the first usable address by default."""
    return str(net.network_address + 1) if net.num_addresses > 2 else None


def _is_infrastructure(ip: str, cfg: Config) -> bool:
    if ip in infrastructure_ips():
        return True
    for c in cfg.allowed_cidrs:
        try:
            net = ipaddress.ip_network(c, strict=False)
        except ValueError:
            continue
        if ip == _first_host(net):
            return True
    return False


def network_exclusions(cidr: str, extra: Iterable[str] = ()) -> list[str]:
    """Addresses inside ``cidr`` that a sweep of it must skip, sorted.

    Infrastructure (:func:`infrastructure_ips`), the network's first host (Docker's
    default gateway address, excluded even when the routing table can't be read), and
    any ``extra`` addresses configured on the target.
    """
    net = ipaddress.ip_network(cidr, strict=False)
    candidates = set(infrastructure_ips()) | set(extra)
    first = _first_host(net)
    if first:
        candidates.add(first)
    inside = []
    for c in candidates:
        try:
            if ipaddress.ip_address(c) in net:
                inside.append(c)
        except ValueError:
            continue
    return sorted(inside, key=ipaddress.ip_address)


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
        if _is_infrastructure(ip, cfg):
            raise TargetNotAllowed(
                f"host {host!r} resolves to {ip}, the lab network's gateway or this "
                "toolbox — that is the host machine or Redkeep itself, not a lab "
                "target. Refusing (safety gate)."
            )
        return host

    raise TargetNotAllowed(
        f"host {host!r} resolves to {ip}, which is outside lab.allowed_cidrs "
        f"{cfg.allowed_cidrs}. Refusing (safety gate)."
    )


def require_url(url: str, cfg: Config) -> str:
    """Validate a URL target and return it unchanged if allowed."""
    assert_allowed(url, cfg)
    return url
