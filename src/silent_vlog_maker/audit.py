"""
silent_vlog_maker.audit — 11-dimensional clip validation with GPS and timestamp verification.
"""
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ClipAudit:
    """Audit result for a single clip."""
    path: Path
    exists: bool = False
    duration_sec: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    codec: str = ""
    has_audio: bool = False
    pix_fmt: str = ""
    rotation: int = 0
    has_gps: bool = False
    creation_time: str = ""
    is_portrait: bool = False
    is_hdr: bool = False
    warnings: list[str] = field(default_factory=list)


def audit_clip(clip_path: Path) -> ClipAudit:
    """Run full audit on a single clip file.

    Checks: existence, duration, dimensions, codec, audio, rotation,
            GPS metadata, HDR flags, portrait orientation.
    """
    result = ClipAudit(path=clip_path)

    if not clip_path.exists():
        result.warnings.append("file not found")
        return result

    result.exists = True

    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-show_streams", "-show_format",
         "-print_format", "json",
         str(clip_path)],
        capture_output=True, text=True,
    )

    try:
        info = json.loads(r.stdout)
    except json.JSONDecodeError:
        result.warnings.append("ffprobe JSON parse failed")
        return result

    fmt = info.get("format", {})
    streams = info.get("streams", [])

    try:
        result.duration_sec = float(fmt.get("duration", 0))
    except (ValueError, TypeError):
        pass

    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if video_stream:
        result.width = video_stream.get("width", 0)
        result.height = video_stream.get("height", 0)
        result.codec = video_stream.get("codec_name", "")
        result.pix_fmt = video_stream.get("pix_fmt", "")

        fps_str = video_stream.get("r_frame_rate", "0/1")
        try:
            num, den = fps_str.split("/")
            result.fps = float(num) / float(den) if float(den) != 0 else 0.0
        except (ValueError, ZeroDivisionError):
            pass

        rotation = video_stream.get("tags", {}).get("rotate", "0")
        try:
            result.rotation = int(rotation)
        except ValueError:
            pass

        color_transfer = video_stream.get("color_transfer", "")
        result.is_hdr = color_transfer in ("smpte2084", "arib-std-b67", "hlg")

        effective_w = result.height if abs(result.rotation) in (90, 270) else result.width
        effective_h = result.width if abs(result.rotation) in (90, 270) else result.height
        result.is_portrait = effective_h > effective_w

    result.has_audio = audio_stream is not None

    tags = fmt.get("tags", {})
    result.creation_time = tags.get("creation_time", "")

    location = tags.get("location", "") or tags.get("com.apple.quicktime.location.ISO6709", "")
    result.has_gps = bool(location)

    if result.duration_sec < 1.0:
        result.warnings.append(f"very short clip ({result.duration_sec:.2f}s)")
    if result.codec not in ("h264", "hevc", "prores", ""):
        result.warnings.append(f"unusual codec: {result.codec}")
    if not result.is_portrait and result.width > 0:
        result.warnings.append("clip is landscape — normalize_to_portrait() needed")

    return result


def audit_clips(clip_paths: list[Path]) -> list[ClipAudit]:
    """Audit multiple clips and return list of ClipAudit results."""
    return [audit_clip(p) for p in clip_paths]


def print_audit_results(results: list[ClipAudit]) -> None:
    """Print human-readable audit report for a list of clips."""
    print("=" * 60)
    print(f"Clip Audit — {len(results)} clip(s)")
    print("=" * 60)

    for r in results:
        status = "OK" if r.exists and not r.warnings else ("WARN" if r.warnings else "MISSING")
        print(f"\n[{status}] {r.path.name}")
        if r.exists:
            print(f"  Duration: {r.duration_sec:.1f}s  | {r.width}x{r.height} | {r.fps:.1f}fps")
            print(f"  Codec: {r.codec} | pix_fmt: {r.pix_fmt} | audio: {r.has_audio}")
            print(f"  Portrait: {r.is_portrait} | HDR: {r.is_hdr} | GPS: {r.has_gps}")
            if r.creation_time:
                print(f"  Created: {r.creation_time[:19]}")
        for w in r.warnings:
            print(f"  ! {w}")
