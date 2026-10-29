"""Configuration loading for the Redkeep runner."""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import yaml


class Config:
    """Loaded Redkeep config with a few convenience accessors."""

    def __init__(self, data: dict, path: Path):
        self.data = data
        self.path = path

    # --- loading ---------------------------------------------------------------
    @classmethod
    def load(cls, path: str | None = None) -> Config:
        candidate = path or os.environ.get("REDKEEP_CONFIG") or "config.yaml"
        p = Path(candidate)
        if not p.exists():
            raise FileNotFoundError(
                f"config not found: {p}. Copy config.example.yaml to config.yaml "
                f"and edit it (or set REDKEEP_CONFIG)."
            )
        with open(p, encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh) or {}, p)

    # --- accessors -------------------------------------------------------------
    @property
    def allowed_cidrs(self) -> list[str]:
        return list(self.data.get("lab", {}).get("allowed_cidrs", []))

    @property
    def allowed_hosts(self) -> list[str]:
        return list(self.data.get("lab", {}).get("allowed_hosts", []))

    @property
    def targets(self) -> dict:
        return self.data.get("targets", {})

    @property
    def auth(self) -> dict:
        return self.data.get("auth", {}) or {}

    @property
    def defectdojo(self) -> dict:
        return self.data.get("defectdojo", {}) or {}

    def run_dir(self, kind: str) -> Path:
        """A fresh timestamped output directory for a pass of ``kind``."""
        base = Path(self.data.get("output_dir", "reports/output"))
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        d = base / f"{stamp}-{kind}"
        d.mkdir(parents=True, exist_ok=True)
        return d
