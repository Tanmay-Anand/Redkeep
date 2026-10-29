"""Scan-profile loading. Profiles live in runner/profiles/<name>.yaml."""
from __future__ import annotations

from pathlib import Path

import yaml

PROFILE_DIR = Path(__file__).resolve().parent.parent / "profiles"


def load(name: str) -> dict:
    p = PROFILE_DIR / f"{name}.yaml"
    if not p.exists():
        available = ", ".join(sorted(f.stem for f in PROFILE_DIR.glob("*.yaml")))
        raise FileNotFoundError(f"unknown profile {name!r}. Available: {available}")
    with open(p, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
