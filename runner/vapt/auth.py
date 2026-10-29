"""Authentication helper for authenticated API passes.

The target app's auth mechanism (JWT bearer vs session cookie) is confirmed from
the codebase at Phase 4 and then described in config.yaml -> auth. This module turns
that config into either request headers (bearer) or cookies (session) by
performing the configured login call against the LAB target.

Test credentials only — never real user credentials (see RoE).
"""
from __future__ import annotations

from typing import Any

import requests

from .config import Config
from .targets import require_url
from .util import log, warn


def _dig(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(part)]
        else:
            cur = cur[part]
    return cur


def _login(cfg: Config) -> requests.Response:
    a = cfg.auth
    url = require_url(a["login_url"], cfg)       # safety gate
    log(f"auth: logging in at {url}")
    return requests.post(url, json=a.get("login_body", {}), timeout=30)


def auth_headers(cfg: Config) -> dict[str, str]:
    """Return headers to attach for authenticated requests (bearer mode)."""
    a = cfg.auth
    if not a.get("enabled"):
        return {}
    if a.get("type") != "bearer":
        return {}
    resp = _login(cfg)
    if resp.status_code >= 300:
        warn(f"auth login failed ({resp.status_code}); continuing unauthenticated")
        return {}
    try:
        token = _dig(resp.json(), a.get("token_json_path", "token"))
    except Exception as e:
        warn(f"could not extract token via {a.get('token_json_path')!r}: {e}")
        return {}
    header = a.get("header_name", "Authorization")
    prefix = a.get("header_prefix", "Bearer ")
    return {header: f"{prefix}{token}"}


def header_args(cfg: Config) -> list[str]:
    """Headers as repeated ``-H name: value`` CLI args (for zap/schemathesis)."""
    out: list[str] = []
    for k, v in auth_headers(cfg).items():
        out += ["-H", f"{k}: {v}"]
    return out
