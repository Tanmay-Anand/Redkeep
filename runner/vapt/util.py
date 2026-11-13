"""Shared helpers: logging and subprocess execution."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

try:
    from rich.console import Console
    _console = Console()

    def log(msg: str) -> None:
        _console.print(f"[bold cyan][redkeep][/] {msg}")

    def warn(msg: str) -> None:
        _console.print(f"[bold yellow][redkeep][/] {msg}")

    def err(msg: str) -> None:
        _console.print(f"[bold red][redkeep][/] {msg}")
except Exception:  # rich optional
    def log(msg: str) -> None:
        print(f"[redkeep] {msg}")

    def warn(msg: str) -> None:
        print(f"[redkeep][warn] {msg}")

    def err(msg: str) -> None:
        print(f"[redkeep][err] {msg}")


class ToolMissing(RuntimeError):
    """Raised when a required external tool is not on PATH."""


def ensure_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise ToolMissing(
            f"required tool {name!r} not found on PATH. Run inside the Kali "
            f"toolbox (lab/kali) where it is installed."
        )
    return path


TIMEOUT_RC = 124


def _as_text(data: bytes | str | None) -> str:
    """TimeoutExpired carries bytes even when the run used text=True."""
    if data is None:
        return ""
    return data.decode("utf-8", "replace") if isinstance(data, bytes) else data


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = False,
        timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a command, streaming a one-line summary. Returns the completed proc.

    ``check=False`` by default because scanners routinely exit non-zero when
    they find issues; callers decide what a failure means.
    """
    log("$ " + " ".join(cmd))
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        # One slow tool must not end the engagement: subprocess has already killed it,
        # so record the timeout and let the caller carry on with whatever output exists
        # (later passes and the report still run). 124 is the conventional timeout code.
        warn(f"{cmd[0]} timed out after {timeout}s and was stopped; continuing with "
             "any partial output")
        proc = subprocess.CompletedProcess(cmd, TIMEOUT_RC, _as_text(e.stdout),
                                           _as_text(e.stderr))
        if check:
            raise subprocess.CalledProcessError(proc.returncode, cmd,
                                                proc.stdout, proc.stderr) from None
        return proc
    if proc.returncode != 0:
        warn(f"{cmd[0]} exited {proc.returncode}")
        if proc.stderr:
            warn(proc.stderr.strip()[:2000])
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd,
                                            proc.stdout, proc.stderr)
    return proc
