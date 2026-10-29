"""Redkeep runner CLI — `vapt`.

Subcommands:
    vapt network   run the network pass
    vapt web       run the web-application pass
    vapt api       run the API pass
    vapt run       run all three (full engagement)
    vapt report    build an offline HTML report from a run directory

Every pass validates targets through the allowlist gate (vapt.targets) before
any tool runs. Findings are written to a timestamped run directory and, if
defectdojo.enabled is true, ingested into DefectDojo; `vapt report` builds a
standalone HTML report without needing the hub.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import Config
from .targets import TargetNotAllowed
from .util import err, log


def _dispatch(cfg: Config, profile_name: str, domains: list[str],
              do_report: bool) -> Path:
    # Imported here so `vapt --help` / arg parsing works without the scanner deps.
    from . import api, ingest, network, profiles, report, web

    prof = profiles.load(profile_name)
    run_dir = cfg.run_dir("-".join(domains))
    log(f"profile={profile_name} domains={','.join(domains)} out={run_dir}")

    results = []
    if "network" in domains:
        results += network.run_pass(cfg, run_dir, prof.get("network", {}) or {})
    if "web" in domains:
        results += web.run_pass(cfg, run_dir, prof.get("web", {}) or {})
    if "api" in domains:
        results += api.run_pass(cfg, run_dir, prof.get("api", {}) or {})

    ingest.import_all(cfg, results)
    if do_report:
        report.build_offline(cfg, run_dir)
    log(f"done. output in {run_dir}")
    return run_dir


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="vapt", description="Redkeep VAPT runner")
    ap.add_argument("--config", default=None, help="path to config.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    for name in ("network", "web", "api"):
        sp = sub.add_parser(name, help=f"run the {name} pass")
        sp.add_argument("--profile", default=name)
        sp.add_argument("--report", action="store_true", help="also build an offline report")

    sp_run = sub.add_parser("run", help="run all passes (network + web + api)")
    sp_run.add_argument("--profile", default="full")
    sp_run.add_argument("--no-report", action="store_true", help="skip the offline report")

    sp_rep = sub.add_parser("report", help="build an offline HTML report")
    sp_rep.add_argument("--run-dir", default=None, help="run directory (default: latest)")

    args = ap.parse_args(argv)

    try:
        cfg = Config.load(args.config)
    except FileNotFoundError as e:
        err(str(e))
        return 2

    try:
        if args.cmd in ("network", "web", "api"):
            _dispatch(cfg, args.profile, [args.cmd], do_report=args.report)
        elif args.cmd == "run":
            _dispatch(cfg, args.profile, ["network", "web", "api"],
                      do_report=not args.no_report)
        elif args.cmd == "report":
            from . import report
            report.build_offline(cfg, Path(args.run_dir) if args.run_dir else None)
    except TargetNotAllowed as e:
        err(f"SAFETY GATE: {e}")
        return 3
    except KeyboardInterrupt:
        err("interrupted")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
