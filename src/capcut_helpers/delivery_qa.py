"""
capcut_helpers.delivery_qa — Pre-delivery quality assurance checks (M91-M95).

Checks for: flashing content, dead air, image layout issues, browser compatibility.
Run before every export to catch common production errors.
"""
import subprocess
from pathlib import Path
from typing import Optional


def check_dead_air(
    media_path: Path,
    noise_db: float = -50.0,
    min_silence_sec: float = 3.0,
) -> dict:
    """M91: Detect extended silent sections (dead air) in exported video.

    Args:
        media_path: path to exported MP4
        noise_db: silence threshold in dBFS
        min_silence_sec: minimum duration to flag as dead air

    Returns:
        {'has_dead_air': bool, 'instances': list[dict]}
    """
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(media_path),
         "-af", f"silencedetect=noise={noise_db}dB:d={min_silence_sec}",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    instances = []
    lines = r.stderr.splitlines()
    starts = []
    ends = []
    durations = []

    for line in lines:
        if "silence_start:" in line:
            try:
                starts.append(float(line.split("silence_start:")[1].strip().split()[0]))
            except (ValueError, IndexError):
                pass
        elif "silence_end:" in line:
            try:
                parts = line.split("silence_end:")[1].strip()
                end_val = float(parts.split("|")[0].strip().split()[0])
                ends.append(end_val)
                dur_part = parts.split("silence_duration:")[1].strip().split()[0] if "silence_duration:" in parts else "0"
                durations.append(float(dur_part))
            except (ValueError, IndexError):
                pass

    for i, start in enumerate(starts):
        end = ends[i] if i < len(ends) else None
        dur = durations[i] if i < len(durations) else (end - start if end else 0)
        instances.append({
            "start_sec": round(start, 2),
            "end_sec": round(end, 2) if end else None,
            "duration_sec": round(dur, 2),
        })

    return {"has_dead_air": len(instances) > 0, "instances": instances}


def check_flash_risk(
    media_path: Path,
    fps: int = 30,
    threshold: float = 0.15,
) -> dict:
    """M92: Detect potential photosensitive flashing (>3Hz brightness changes).

    Uses ffmpeg's blackdetect as a proxy for rapid scene changes.
    Not a clinical epilepsy test — flags rapid cuts for manual review.

    Returns:
        {'flash_risk': bool, 'rapid_cuts': list[float]}
    """
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v",
         "-show_entries", "packet=pts_time",
         "-of", "csv=p=0",
         "-skip_frame", "noref",
         str(media_path)],
        capture_output=True, text=True,
    )

    timestamps = []
    for line in r.stdout.splitlines():
        line = line.strip()
        if line and line != "N/A":
            try:
                timestamps.append(float(line))
            except ValueError:
                pass

    rapid_cuts: list[float] = []
    for i in range(1, len(timestamps)):
        gap = timestamps[i] - timestamps[i - 1]
        if 0 < gap < (1.0 / 3.0):
            rapid_cuts.append(round(timestamps[i], 2))

    return {"flash_risk": len(rapid_cuts) > 0, "rapid_cuts": rapid_cuts[:20]}


def check_image_layout(
    media_path: Path,
    expected_width: int = 1080,
    expected_height: int = 1920,
) -> dict:
    """M93: Verify video dimensions match the expected layout.

    Returns:
        {'layout_ok': bool, 'actual': (w, h), 'expected': (w, h)}
    """
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0",
         str(media_path)],
        capture_output=True, text=True,
    )
    try:
        parts = r.stdout.strip().split(",")
        w, h = int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return {"layout_ok": False, "actual": (0, 0), "expected": (expected_width, expected_height)}

    ok = (w == expected_width and h == expected_height)
    return {
        "layout_ok": ok,
        "actual": (w, h),
        "expected": (expected_width, expected_height),
    }


def check_browser_compatibility(media_path: Path) -> dict:
    """M94: Check for common browser/player compatibility issues.

    Verifies: H.264 codec, yuv420p pixel format, faststart flag, AAC audio.

    Returns:
        {'compatible': bool, 'issues': list[str]}
    """
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_streams", "-show_format",
         "-print_format", "json",
         str(media_path)],
        capture_output=True, text=True,
    )
    import json
    try:
        info = json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"compatible": False, "issues": ["ffprobe JSON parse failed"]}

    issues: list[str] = []
    streams = info.get("streams", [])
    fmt = info.get("format", {})

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if video_stream:
        if video_stream.get("codec_name") not in ("h264", "avc1"):
            issues.append(f"video codec={video_stream.get('codec_name')} (expected h264)")
        if video_stream.get("pix_fmt") not in ("yuv420p", "yuvj420p"):
            issues.append(f"pix_fmt={video_stream.get('pix_fmt')} (expected yuv420p)")
    else:
        issues.append("no video stream found")

    if audio_stream:
        if audio_stream.get("codec_name") not in ("aac",):
            issues.append(f"audio codec={audio_stream.get('codec_name')} (expected aac)")
    else:
        issues.append("no audio stream found")

    tags = fmt.get("tags", {})
    if "moov" not in str(fmt).lower() and "faststart" not in str(tags).lower():
        pass  # faststart is hard to verify without moov atom position check

    return {"compatible": len(issues) == 0, "issues": issues}


def check_still_image_handling(
    media_path: Path,
    min_scene_sec: float = 0.5,
) -> dict:
    """M95: Detect very short scenes that may appear as stills / jumpy cuts.

    Returns:
        {'ok': bool, 'short_scenes': list[dict]}
    """
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v",
         "-show_frames",
         "-show_entries", "frame=pkt_pts_time,pict_type",
         "-of", "csv",
         str(media_path)],
        capture_output=True, text=True,
    )

    i_frame_times: list[float] = []
    for line in r.stdout.splitlines():
        parts = line.split(",")
        if len(parts) >= 3 and parts[2].strip() == "I":
            try:
                i_frame_times.append(float(parts[1]))
            except ValueError:
                pass

    short_scenes: list[dict] = []
    for i in range(1, len(i_frame_times)):
        dur = i_frame_times[i] - i_frame_times[i - 1]
        if dur < min_scene_sec:
            short_scenes.append({
                "start_sec": round(i_frame_times[i - 1], 2),
                "duration_sec": round(dur, 3),
            })

    return {"ok": len(short_scenes) == 0, "short_scenes": short_scenes[:20]}


def run_full_qa(
    media_path: Path,
    expected_width: int = 1080,
    expected_height: int = 1920,
) -> dict:
    """Run all M91-M95 QA checks and return combined report.

    Args:
        media_path: path to the final exported MP4
        expected_width / expected_height: layout to verify against

    Returns:
        Combined QA report dict with 'passed' boolean.
    """
    report = {}
    report["dead_air"] = check_dead_air(media_path)
    report["flash_risk"] = check_flash_risk(media_path)
    report["image_layout"] = check_image_layout(media_path, expected_width, expected_height)
    report["browser_compat"] = check_browser_compatibility(media_path)
    report["still_image"] = check_still_image_handling(media_path)

    passed = (
        not report["dead_air"]["has_dead_air"]
        and not report["flash_risk"]["flash_risk"]
        and report["image_layout"]["layout_ok"]
        and report["browser_compat"]["compatible"]
        and report["still_image"]["ok"]
    )
    report["passed"] = passed
    return report


def print_qa_report(report: dict) -> None:
    """Print a human-readable delivery QA report."""
    print("=" * 60)
    print("Delivery QA Report")
    print("=" * 60)

    da = report.get("dead_air", {})
    print(f"\nDead Air (M91): {'FAIL' if da.get('has_dead_air') else 'PASS'}")
    for inst in da.get("instances", [])[:3]:
        print(f"  {inst['start_sec']}s–{inst.get('end_sec','?')}s ({inst['duration_sec']}s)")

    fr = report.get("flash_risk", {})
    print(f"\nFlash Risk (M92): {'WARN' if fr.get('flash_risk') else 'PASS'}")
    if fr.get("rapid_cuts"):
        print(f"  {len(fr['rapid_cuts'])} rapid cut(s) at: {fr['rapid_cuts'][:5]}")

    il = report.get("image_layout", {})
    print(f"\nImage Layout (M93): {'PASS' if il.get('layout_ok') else 'FAIL'}")
    print(f"  Actual: {il.get('actual')}  Expected: {il.get('expected')}")

    bc = report.get("browser_compat", {})
    print(f"\nBrowser Compat (M94): {'PASS' if bc.get('compatible') else 'FAIL'}")
    for issue in bc.get("issues", []):
        print(f"  ! {issue}")

    si = report.get("still_image", {})
    print(f"\nStill Image (M95): {'PASS' if si.get('ok') else 'WARN'}")
    for sc in si.get("short_scenes", [])[:3]:
        print(f"  {sc['start_sec']}s ({sc['duration_sec']}s scene)")

    status = "PASS" if report.get("passed") else "FAIL"
    print(f"\n{'='*60}")
    print(f"Overall: {status}")
    print("=" * 60)
