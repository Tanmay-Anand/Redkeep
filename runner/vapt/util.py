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


def run(cmd: list[str], *, cwd: Path | None = None, check: bool = False,
        timeout: int | None = None) -> subprocess.CompletedProcess:
    """Run a command, streaming a one-line summary. Returns the completed proc.

    ``check=False`` by default because scanners routinely exit non-zero when
    they find issues; callers decide what a failure means.
    """
    log("$ " + " ".join(cmd))
    proc = subprocess.run(
        cmd, cwd=str(cwd) if cwd else None,
        capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        warn(f"{cmd[0]} exited {proc.returncode}")
        if proc.stderr:
            warn(proc.stderr.strip()[:2000])
    if check and proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd,
                                            proc.stdout, proc.stderr)
    return proc
