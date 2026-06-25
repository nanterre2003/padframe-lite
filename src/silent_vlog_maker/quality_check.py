"""
silent_vlog_maker.quality_check — Output verification for exported videos.
"""
import json
import subprocess
from pathlib import Path
from typing import Optional


def verify_output(
    output_path: Path,
    expected_width: int = 1080,
    expected_height: int = 1920,
    expected_fps: float = 30.0,
    min_duration_sec: float = 1.0,
    max_duration_sec: float = 3600.0,
    require_audio: bool = True,
) -> dict:
    """Verify that an exported video meets expected specs.

    Returns:
        {
            'passed': bool,
            'issues': list[str],
            'info': dict,
        }
    """
    issues: list[str] = []

    if not output_path.exists():
        return {"passed": False, "issues": ["output file does not exist"], "info": {}}

    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_streams", "-show_format",
         "-print_format", "json",
         str(output_path)],
        capture_output=True, text=True,
    )

    try:
        info = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"passed": False, "issues": ["ffprobe failed"], "info": {}}

    fmt = info.get("format", {})
    streams = info.get("streams", [])

    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

    try:
        duration = float(fmt.get("duration", 0))
    except (ValueError, TypeError):
        duration = 0.0

    extracted = {
        "duration_sec": duration,
        "width": video.get("width", 0) if video else 0,
        "height": video.get("height", 0) if video else 0,
        "codec": video.get("codec_name", "") if video else "",
        "pix_fmt": video.get("pix_fmt", "") if video else "",
        "has_audio": audio is not None,
        "file_size_mb": output_path.stat().st_size // (1024 * 1024),
    }

    if not video:
        issues.append("no video stream")
    else:
        if extracted["width"] != expected_width or extracted["height"] != expected_height:
            issues.append(
                f"dimensions {extracted['width']}×{extracted['height']} "
                f"≠ expected {expected_width}×{expected_height}"
            )
        if extracted["codec"] not in ("h264", "hevc"):
            issues.append(f"codec {extracted['codec']!r} not h264/hevc")
        if extracted["pix_fmt"] not in ("yuv420p", "yuvj420p"):
            issues.append(f"pix_fmt {extracted['pix_fmt']!r} not yuv420p")

    if require_audio and not audio:
        issues.append("no audio stream")

    if duration < min_duration_sec:
        issues.append(f"duration {duration:.1f}s < minimum {min_duration_sec}s")
    if duration > max_duration_sec:
        issues.append(f"duration {duration:.1f}s > maximum {max_duration_sec}s")

    return {"passed": len(issues) == 0, "issues": issues, "info": extracted}


def print_quality_check(result: dict) -> None:
    """Print quality check results."""
    status = "PASS" if result.get("passed") else "FAIL"
    print(f"\nQuality Check: [{status}]")
    info = result.get("info", {})
    if info:
        print(f"  {info.get('width')}×{info.get('height')} | "
              f"{info.get('duration_sec', 0):.1f}s | "
              f"{info.get('codec')} | "
              f"{info.get('file_size_mb')}MB")
    for issue in result.get("issues", []):
        print(f"  ! {issue}")
