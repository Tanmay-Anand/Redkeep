#!/usr/bin/env python3
"""Redkeep launcher UI — a dependency-free local control panel.

Started by start-redkeep.sh / start-redkeep.bat. Serves a small dashboard at
http://127.0.0.1:8765 (localhost only) that lets you start/stop the isolated
lab, run scans, and open reports — all by shelling out to `docker compose` and
the already-safety-gated `vapt` runner. Uses only the Python standard library,
binds to loopback, and exits when you close the window: nothing is left running.

Commands are chosen from a fixed whitelist (no arbitrary shell), so the UI can
only do the lab/scan actions defined below.
"""
from __future__ import annotations

import argparse
import contextlib
import json
import subprocess
import threading
import time
import webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
UI_DIR = REPO_ROOT / "ui"
LAB = ["docker", "compose", "-f", "lab/docker-compose.yml"]
HUB = ["docker", "compose", "-f", "hub/docker-compose.yml"]
TARGETS = ["target-db", "target-api", "target-platform",
           "target-admin", "target-reports", "target-ui"]
JOB_DIR = REPO_ROOT / "reports" / "output" / ".jobs"
VALID_DOMAINS = {"run", "network", "web", "api"}
# Teardown actions may interrupt a running job (e.g. a slow/stuck lab-up).
TEARDOWN_ACTIONS = {"lab-down", "down-all"}

# ---- job state (one job at a time keeps resource use low) --------------------
_lock = threading.Lock()
_job: dict = {"status": "idle", "label": "", "logfile": None,
              "started": None, "returncode": None, "proc": None}


def _command_for(kind: str, params: dict) -> tuple[list[str], str]:
    """Map a UI action to a concrete command (whitelist — no arbitrary input)."""
    if kind == "lab-up":
        return LAB + ["up", "-d", *TARGETS], "Start lab target"
    if kind == "lab-down":
        return LAB + ["down"], "Stop lab target"
    if kind == "down-all":
        return LAB + ["down"], "Stop everything"
    if kind == "report":
        return LAB + ["run", "--rm", "kali", "vapt", "report"], "Rebuild report"
    if kind == "scan":
        domain = params.get("domain", "run")
        if domain not in VALID_DOMAINS:
            raise ValueError(f"invalid domain {domain!r}")
        profile = str(params.get("profile", "quick"))
        if not profile.isalnum():
            raise ValueError("invalid profile")
        return (LAB + ["run", "--rm", "kali", "vapt", domain, "--profile", profile],
                f"Scan: {domain} ({profile})")
    raise ValueError(f"unknown action {kind!r}")


def _run_job(cmd: list[str], label: str) -> None:
    JOB_DIR.mkdir(parents=True, exist_ok=True)
    logfile = JOB_DIR / f"job-{datetime.now():%Y%m%d-%H%M%S}.log"
    with _lock:
        _job.update(status="running", label=label, logfile=str(logfile),
                    started=time.time(), returncode=None)
    with open(logfile, "w", encoding="utf-8") as fh:
        fh.write(f"$ {' '.join(cmd)}\n\n")
        fh.flush()
        try:
            proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT), stdout=fh,
                                    stderr=subprocess.STDOUT, text=True)
            with _lock:
                _job["proc"] = proc
            rc = proc.wait()
        except FileNotFoundError:
            fh.write("\n[error] 'docker' not found on PATH. Is Docker Desktop installed?\n")
            rc = 127
        except Exception as e:  # pragma: no cover
            fh.write(f"\n[error] {e}\n")
            rc = 1
    with _lock:
        _job.update(status="done", returncode=rc, proc=None)


def _terminate_running(timeout: float = 8.0) -> None:
    """Terminate the current job's process and wait (bounded) for it to finish.

    Lets a teardown action interrupt a slow or stuck job (e.g. a 'Start lab' that
    is still pulling/building images) instead of the teardown being refused.
    """
    with _lock:
        proc = _job.get("proc")
    if proc is not None:
        with contextlib.suppress(Exception):
            proc.terminate()
    deadline = time.time() + timeout
    while time.time() < deadline:
        with _lock:
            if _job["status"] != "running":
                return
        time.sleep(0.1)


def _start_job(kind: str, params: dict) -> tuple[int, dict]:
    with _lock:
        running = _job["status"] == "running"
    if running:
        if kind in TEARDOWN_ACTIONS:
            _terminate_running()          # teardown preempts a running job
        else:
            return 409, {"error": "a job is already running — stop it first"}
    try:
        cmd, label = _command_for(kind, params)
    except ValueError as e:
        return 400, {"error": str(e)}
    threading.Thread(target=_run_job, args=(cmd, label), daemon=True).start()
    return 200, {"ok": True, "label": label}


def _docker_ok() -> bool:
    try:
        r = subprocess.run(["docker", "info"], capture_output=True, timeout=8)
        return r.returncode == 0
    except Exception:
        return False


def _profiles() -> list[str]:
    d = REPO_ROOT / "runner" / "profiles"
    return sorted(p.stem for p in d.glob("*.yaml")) if d.exists() else []


def _targets() -> dict:
    cfg = REPO_ROOT / "config.yaml"
    if not cfg.exists():
        return {"configured": False}
    try:
        import yaml  # optional on host
        data = yaml.safe_load(cfg.read_text(encoding="utf-8")) or {}
        t = data.get("targets", {})
        return {"configured": True,
                "web": [x.get("name") for x in t.get("web", [])],
                "api": [x.get("name") for x in t.get("api", [])],
                "network": [x.get("name") for x in t.get("network", [])],
                "defectdojo": bool(data.get("defectdojo", {}).get("enabled"))}
    except Exception:
        return {"configured": True, "note": "install pyyaml to show targets"}


def _runs() -> list[dict]:
    base = REPO_ROOT / "reports" / "output"
    if not base.exists():
        return []
    out = []
    for d in sorted((p for p in base.iterdir() if p.is_dir() and not p.name.startswith(".")),
                    reverse=True)[:25]:
        entry = {"name": d.name, "report": (d / "report.html").exists()}
        sj = d / "summary.json"
        if sj.exists():
            try:
                data = json.loads(sj.read_text(encoding="utf-8"))
                entry["counts"] = data.get("counts")
                entry["total"] = data.get("total")
            except (OSError, json.JSONDecodeError):
                pass
        out.append(entry)
    return out


def _job_view() -> dict:
    with _lock:
        j = dict(_job)
    log = ""
    if j.get("logfile") and Path(j["logfile"]).exists():
        log = Path(j["logfile"]).read_text(encoding="utf-8", errors="replace")[-8000:]
    return {"status": j["status"], "label": j["label"],
            "returncode": j["returncode"], "log": log}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):  # quiet
        pass

    def _send(self, code, body, ctype="application/json"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body).encode()
        elif isinstance(body, str):
            body = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, path: Path, ctype: str):
        if not path.exists() or not path.is_file():
            return self._send(404, {"error": "not found"})
        self._send(200, path.read_bytes(), ctype)

    def do_GET(self):
        p = urlparse(self.path).path
        if p == "/" or p == "/index.html":
            return self._serve_file(UI_DIR / "index.html", "text/html; charset=utf-8")
        if p == "/api/status":
            return self._send(200, {"docker": _docker_ok(), "profiles": _profiles(),
                                    "targets": _targets(), "runs": _runs()})
        if p == "/api/job":
            return self._send(200, _job_view())
        if p.startswith("/resources/"):
            fp = (REPO_ROOT / p.lstrip("/")).resolve()
            if str(fp).startswith(str((REPO_ROOT / "resources").resolve())):
                ext = fp.suffix.lower()
                ctype = {".svg": "image/svg+xml", ".png": "image/png",
                         ".ico": "image/x-icon", ".woff2": "font/woff2",
                         ".txt": "text/plain; charset=utf-8"}.get(ext, "application/octet-stream")
                return self._serve_file(fp, ctype)
        if p.startswith("/report/"):
            fp = (REPO_ROOT / "reports" / "output" / p[len("/report/"):]).resolve()
            base = (REPO_ROOT / "reports" / "output").resolve()
            if str(fp).startswith(str(base)) and fp.exists():
                return self._serve_file(fp, "text/html; charset=utf-8")
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        p = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0) or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "bad json"})
        if p == "/api/exec":
            code, resp = _start_job(body.get("action", ""), body)
            return self._send(code, resp)
        if p == "/api/stop":
            with _lock:
                proc = _job.get("proc")
            if proc:
                proc.terminate()
                return self._send(200, {"ok": True})
            return self._send(200, {"ok": False, "note": "no job running"})
        return self._send(404, {"error": "not found"})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()

    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    url = f"http://127.0.0.1:{args.port}/"
    print(f"[redkeep] UI on {url}  (Ctrl+C to stop — nothing stays running)")
    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[redkeep] UI stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
