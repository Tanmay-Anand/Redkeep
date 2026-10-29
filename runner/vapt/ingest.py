"""Ingest scan output into DefectDojo via the import-scan API.

DefectDojo is OPTIONAL. It is a heavy multi-container stack, so Redkeep does not
require it: by default scans just write raw output and `vapt report` builds an
offline HTML report. Ingestion runs only when ``defectdojo.enabled`` is true in
config.yaml (or ``--ingest`` is passed), i.e. when you deliberately bring the
hub up for cross-run tracking.

Each pass produces one or more :class:`ScanResult` objects; :func:`import_all`
pushes them into the configured engagement. ``scan_type`` values must match
DefectDojo's parser names (e.g. "Nmap Scan", "ZAP Scan", "Nikto Scan",
"Nuclei Scan").
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import requests

from .config import Config
from .util import err, log, warn


@dataclass
class ScanResult:
    scan_type: str      # DefectDojo parser name
    path: Path          # file to upload
    title: str          # human label for the test


def enabled(cfg: Config) -> bool:
    return bool(cfg.defectdojo.get("enabled"))


def _dd(cfg: Config):
    dd = cfg.defectdojo
    if not dd.get("url") or not dd.get("api_token"):
        raise RuntimeError("defectdojo.url and defectdojo.api_token must be set in config.yaml")
    base = dd["url"].rstrip("/") + "/api/v2"
    headers = {"Authorization": f"Token {dd['api_token']}"}
    return base, headers, dd


def _engagement_id(base, headers, dd) -> int:
    if dd.get("engagement_id"):
        return int(dd["engagement_id"])
    r = requests.get(f"{base}/engagements/", headers=headers,
                     params={"name": dd["engagement_name"]}, timeout=30)
    r.raise_for_status()
    for e in r.json().get("results", []):
        if e["name"] == dd["engagement_name"]:
            return e["id"]
    raise RuntimeError(
        f"engagement {dd['engagement_name']!r} not found — run hub/config/bootstrap.py first"
    )


def import_one(cfg: Config, result: ScanResult) -> bool:
    if not result.path.exists() or result.path.stat().st_size == 0:
        warn(f"skip ingest: {result.path.name} is missing/empty")
        return False
    base, headers, dd = _dd(cfg)
    eid = _engagement_id(base, headers, dd)
    with open(result.path, "rb") as fh:
        files = {"file": (result.path.name, fh)}
        data = {
            "scan_type": result.scan_type,
            "engagement": eid,
            "test_title": result.title,
            "active": "true",
            "verified": "false",
            "close_old_findings": "false",
        }
        r = requests.post(f"{base}/import-scan/", headers=headers,
                          data=data, files=files, timeout=120)
    if r.status_code >= 300:
        err(f"ingest failed for {result.title}: {r.status_code} {r.text[:500]}")
        return False
    log(f"ingested {result.title} ({result.scan_type})")
    return True


def import_all(cfg: Config, results: list[ScanResult]) -> int:
    if not enabled(cfg):
        warn("defectdojo.enabled is false — skipping ingestion (offline report only). "
             "Set it true and bring up hub/ to track findings in DefectDojo.")
        return 0
    ok = 0
    for res in results:
        try:
            if import_one(cfg, res):
                ok += 1
        except Exception as e:  # keep going; one bad result shouldn't stop the rest
            err(f"ingest error for {res.title}: {e}")
    log(f"ingested {ok}/{len(results)} result(s) into DefectDojo")
    return ok
