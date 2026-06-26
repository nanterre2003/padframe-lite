"""
silent_vlog_maker.asset_scanner — Background music, fonts, and template inventory.
"""
import os
import subprocess
from pathlib import Path
from typing import Optional


_AUDIO_EXTENSIONS = {".mp3", ".m4a", ".aac", ".wav", ".flac", ".ogg"}
_FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".woff"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi", ".webm"}


def scan_bgm(
    bgm_dir: Path,
    min_duration_sec: float = 30.0,
) -> list[dict]:
    """Scan a directory for background music tracks.

    Args:
        bgm_dir: directory to scan
        min_duration_sec: minimum track length to include

    Returns: list of {path, duration_sec, name}
    """
    results = []
    if not bgm_dir.exists():
        return results

    for p in sorted(bgm_dir.iterdir()):
        if p.suffix.lower() not in _AUDIO_EXTENSIONS:
            continue
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(p)],
            capture_output=True, text=True,
        )
        try:
            dur = float(r.stdout.strip())
        except ValueError:
            dur = 0.0
        if dur >= min_duration_sec:
            results.append({"path": p, "duration_sec": dur, "name": p.stem})

    return results


def scan_fonts(font_dirs: Optional[list[Path]] = None) -> list[dict]:
    """Scan standard font directories for available fonts.

    Args:
        font_dirs: additional directories to scan (beyond system defaults)

    Returns: list of {path, name, family}
    """
    search_dirs: list[Path] = [
        Path("assets/fonts"),
        Path.home() / "AppData" / "Local" / "Microsoft" / "Windows" / "Fonts",
        Path("C:/Windows/Fonts"),
        Path("/System/Library/Fonts"),
        Path("/usr/share/fonts"),
    ]
    if font_dirs:
        search_dirs.extend(font_dirs)

    results = []
    seen: set[str] = set()

    for d in search_dirs:
        if not d.exists():
            continue
        for p in d.rglob("*"):
            if p.suffix.lower() not in _FONT_EXTENSIONS:
                continue
            key = p.stem.lower()
            if key not in seen:
                seen.add(key)
                results.append({
                    "path": p,
                    "name": p.stem,
                    "family": p.parent.name,
                })

    return results


def scan_templates(template_dir: Path) -> list[dict]:
    """Scan a directory for CapCut draft templates (.json backups).

    Returns: list of {path, name, size_kb}
    """
    results = []
    if not template_dir.exists():
        return results

    for p in sorted(template_dir.rglob("*.json")):
        if "draft_content" in p.name or "draft_info" in p.name:
            size_kb = p.stat().st_size // 1024
            results.append({
                "path": p,
                "name": p.parent.name or p.stem,
                "size_kb": size_kb,
            })

    return results


def scan_footage(
    footage_dir: Path,
    recursive: bool = True,
) -> list[dict]:
    """Scan a directory for raw footage files.

    Returns: list of {path, name, extension}
    """
    results = []
    if not footage_dir.exists():
        return results

    iterator = footage_dir.rglob("*") if recursive else footage_dir.iterdir()
    for p in sorted(iterator):
        if p.suffix.lower() in _VIDEO_EXTENSIONS and p.is_file():
            results.append({
                "path": p,
                "name": p.stem,
                "extension": p.suffix.lower(),
            })

    return results


def inventory_project(project_root: Path) -> dict:
    """Run a full asset inventory of a project directory.

    Returns:
        {
            'bgm': list of BGM tracks,
            'fonts': list of fonts,
            'templates': list of CapCut templates,
            'footage': list of raw footage files,
        }
    """
    return {
        "bgm": scan_bgm(project_root / "assets" / "bgm"),
        "fonts": scan_fonts([project_root / "assets" / "fonts"]),
        "templates": scan_templates(project_root / "assets" / "templates"),
        "footage": scan_footage(project_root / "videos"),
    }


def print_inventory(inv: dict) -> None:
    """Print asset inventory summary."""
    print("=" * 60)
    print("Asset Inventory")
    print("=" * 60)
    print(f"\nBGM tracks: {len(inv.get('bgm', []))}")
    for t in inv.get("bgm", [])[:5]:
        print(f"  {t['name']} ({t['duration_sec']:.1f}s)")

    print(f"\nFonts: {len(inv.get('fonts', []))}")
    for f in inv.get("fonts", [])[:5]:
        print(f"  {f['name']}")

    print(f"\nTemplates: {len(inv.get('templates', []))}")
    for t in inv.get("templates", [])[:5]:
        print(f"  {t['name']} ({t['size_kb']}kb)")

    print(f"\nFootage files: {len(inv.get('footage', []))}")
    for f in inv.get("footage", [])[:5]:
        print(f"  {f['name']}{f['extension']}")
