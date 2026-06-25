"""
capcut_helpers.paths — Standard CapCut Desktop path resolution.

Auto-detects for the CURRENT user (no hardcoded username).
Override any path with environment variables.
"""
import os
from pathlib import Path


def _env_path(var: str, default: Path) -> Path:
    """Return env-var path if set, otherwise the default."""
    v = os.environ.get(var)
    return Path(v) if v else default


# ── CapCut user data ──────────────────────────────────────────────────────────
CAPCUT_USER_DATA: Path = _env_path(
    "CAPCUT_USER_DATA",
    Path.home() / "AppData" / "Local" / "CapCut" / "User Data",
)

# CapCut effect resource cache (for effects.py lookups)
EFFECT_CACHE: Path = CAPCUT_USER_DATA / "Resources" / "Effect"

# capcut-cli npm shim (optional — for JSON automation via CLI)
CAPCUT_CLI: Path = _env_path(
    "CAPCUT_CLI",
    Path.home() / "AppData" / "Roaming" / "npm" / "capcut-cli.cmd",
)

# ── Project workspace ─────────────────────────────────────────────────────────
PROJECT_ROOT: Path = _env_path("VIDEO_KIT_PROJECT_ROOT", Path.cwd())

VIDEOS_DIR: Path = PROJECT_ROOT / "videos"
ASSETS_DIR: Path = PROJECT_ROOT / "assets"

# ── Draft locations ───────────────────────────────────────────────────────────
DRAFTS_ROOT: Path = CAPCUT_USER_DATA / "Projects" / "com.lveditor.draft"


def draft_path(project_name: str) -> Path:
    """Resolve full path to a CapCut project draft folder."""
    return DRAFTS_ROOT / project_name


def draft_files(project_name: str) -> dict[str, Path]:
    """Return the 7 JSON files that need to stay in sync (M18 lesson).

    CapCut writes to draft_info.json but reads from draft_content.json.
    When these diverge CapCut silently overwrites newer edits with stale state.
    """
    d = draft_path(project_name)
    tl_dir = d / "Timelines"

    files: dict[str, Path] = {
        "draft_content": d / "draft_content.json",
        "draft_info": d / "draft_info.json",
        "draft_content_bak": d / "draft_content.json.bak",
        "draft_info_bak": d / "draft_info.json.bak",
    }

    # Timeline subdirectory copies (UUID-named folder)
    if tl_dir.exists():
        for sub in tl_dir.iterdir():
            if sub.is_dir():
                files[f"tl_{sub.name}_content"] = sub / "draft_content.json"
                files[f"tl_{sub.name}_info"] = sub / "draft_info.json"
                break  # typically one Timeline subfolder

    return files


def discover_all_draft_jsons(project_name: str) -> list[Path]:
    """Return all JSON-like files that must stay synced.

    Handles Timelines/<UUID>/ subdirs — these silent rollback sources
    were the root cause of M18 data loss incidents.
    """
    d = draft_path(project_name)
    found: list[Path] = []

    for p in d.iterdir():
        if p.suffix in (".json",) and p.is_file():
            found.append(p)

    tl = d / "Timelines"
    if tl.exists():
        for sub in tl.iterdir():
            if sub.is_dir():
                for p in sub.iterdir():
                    if p.suffix == ".json" and p.is_file():
                        found.append(p)

    return found
