import subprocess


def kill_capcut_all() -> tuple[int, str]:
    """Kill all CapCut.exe + helper processes via PowerShell.

    Returns:
        (return_code, stdout) — 0 if success or no processes running.

    M20: must run BEFORE editing draft JSON externally. Otherwise CapCut's
    auto-save (cached in-memory state) will overwrite your file on next save.
    """
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-Process CapCut -ErrorAction SilentlyContinue | Stop-Process -Force; "
         "Get-Process CapCutHelper -ErrorAction SilentlyContinue | Stop-Process -Force"],
        capture_output=True, text=True
    )
    return result.returncode, result.stdout + result.stderr


def is_capcut_running() -> bool:
    """Check if any CapCut process is alive (post-kill verification)."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "(Get-Process CapCut -ErrorAction SilentlyContinue).Count"],
        capture_output=True, text=True
    )
    try:
        return int(result.stdout.strip()) > 0
    except (ValueError, AttributeError):
        return False


def safe_kill_then_verify(max_retries: int = 3) -> bool:
    """Kill + verify dead. Retry up to N times.

    Returns True if successfully killed all processes, False otherwise.
    """
    import time
    for attempt in range(max_retries):
        kill_capcut_all()
        time.sleep(1.5)
        if not is_capcut_running():
            return True
    return False
