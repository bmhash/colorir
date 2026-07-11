"""Open files in the system's default viewer (WSL2, Linux, macOS, Windows)."""

import platform
import shutil
import subprocess
from pathlib import Path


def open_file(path: Path) -> bool:
    """Open a file in the system's default viewer.

    Auto-detects WSL2 and converts the path to Windows format.
    Returns True if the command was launched, False otherwise.
    """
    path = path.resolve()

    if _is_wsl():
        return _open_wsl(path)
    elif platform.system() == "Darwin":
        return _run(["open", str(path)])
    elif platform.system() == "Windows":
        return _run(["cmd", "/c", "start", "", str(path)])
    else:
        # Linux nativo
        if shutil.which("xdg-open"):
            return _run(["xdg-open", str(path)])
    return False


def _is_wsl() -> bool:
    """Detect if running inside WSL2."""
    try:
        with open("/proc/version") as f:
            return "microsoft" in f.read().lower()
    except OSError:
        return False


# Characters that cmd.exe interprets as shell operators (excludes $ which is bash-only)
_CMD_METACHARACTERS = set('&|<>^%"')


def _open_wsl(path: Path) -> bool:
    """Open a file via Windows from WSL2."""
    # Convert Linux path → Windows UNC path
    try:
        result = subprocess.run(
            ["wslpath", "-w", str(path)],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return False
        win_path = result.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return False

    # Reject paths with cmd.exe shell metacharacters (command injection prevention)
    if _CMD_METACHARACTERS & set(win_path):
        return False

    # Open with cmd.exe /c start
    return _run(["cmd.exe", "/c", "start", "", win_path])


def _run(cmd: list[str]) -> bool:
    """Execute a command without blocking, return True if launched successfully."""
    try:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except OSError:
        return False
