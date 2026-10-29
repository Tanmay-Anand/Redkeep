#!/usr/bin/env python3
"""Bootstrap the DefectDojo product + engagement Redkeep ingests into.

Idempotent: safe to run repeatedly. Reads connection details from config.yaml
(``defectdojo`` section). Creates the product and an open engagement if missing,
and prints their ids.

Usage:
    python hub/config/bootstrap.py [--config config.yaml]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests
import yaml


def load_cfg(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def api(cfg: dict):
    dd = cfg["defectdojo"]
    base = dd["url"].rstrip("/") + "/api/v2"
    headers = {"Authorization": f"Token {dd['api_token']}"}
    return base, headers, dd


def get_or_create_product(base, headers, name) -> int:
    r = requests.get(f"{base}/products/", headers=headers,
                     params={"name": name}, timeout=30)
    r.raise_for_status()
    for p in r.json().get("results", []):
        if p["name"] == name:
            return p["id"]
    r = requests.post(f"{base}/products/", headers=headers, timeout=30, json={
        "name": name,
        "description": "example-app — Redkeep VAPT engagement target.",
        "prod_type": 1,
    })
    r.raise_for_status()
    return r.json()["id"]


def get_or_create_engagement(base, headers, product_id, name) -> int:
    r = requests.get(f"{base}/engagements/", headers=headers,
                     params={"product": product_id, "name": name}, timeout=30)
    r.raise_for_status()
    for e in r.json().get("results", []):
        if e["name"] == name:
            return e["id"]
    from datetime import date
    today = date.today().isoformat()
    r = requests.post(f"{base}/engagements/", headers=headers, timeout=30, json={
        "name": name,
        "product": product_id,
        "target_start": today,
        "target_end": today,
        "status": "In Progress",
        "engagement_type": "Interactive",
    })
    r.raise_for_status()
    return r.json()["id"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    args = ap.parse_args()

    if not Path(args.config).exists():
        print(f"config not found: {args.config} (copy config.example.yaml)", file=sys.stderr)
        return 2

    cfg = load_cfg(args.config)
    base, headers, dd = api(cfg)

    pid = get_or_create_product(base, headers, dd["product_name"])
    eid = get_or_create_engagement(base, headers, pid, dd["engagement_name"])
    print(f"product_id={pid} engagement_id={eid}")
    print("Add engagement_id to config.yaml (defectdojo.engagement_id) if you "
          "want to pin it; otherwise Redkeep resolves it by name.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
