"""
silent_vlog_maker.effects — FFmpeg filter chain builders for video effects.
"""
from typing import Optional

from .constants import CINEMATIC_CURVES


def kenburns_zoom_in(
    duration: float,
    start_scale: float = 1.0,
    end_scale: float = 1.08,
    w: int = 1080,
    h: int = 1920,
) -> str:
    """Slow zoom-in over duration. Returns filter string for portrait/landscape.

    Suitable for photo montage or establishing shots.
    """
    fps = 30
    total_frames = int(duration * fps)
    zoom_step = (end_scale - start_scale) / max(total_frames, 1)
    return (
        f"scale=8000:-1,"
        f"zoompan=z='min(zoom+{zoom_step:.6f},{end_scale})':"
        f"d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={w}x{h},fps={fps}"
    )


def kenburns_pan_right(
    duration: float,
    w: int = 1080,
    h: int = 1920,
    zoom: float = 1.05,
) -> str:
    """Pan-right with slight zoom using zoompan filter."""
    fps = 30
    total_frames = int(duration * fps)
    return (
        f"scale=8000:-1,"
        f"zoompan=z='{zoom}':"
        f"d={total_frames}:"
        f"x='if(lte(on,1),(iw-iw/zoom)/2,x+((iw-iw/zoom)/2-x)/({total_frames}-on+1))':"
        f"y='ih/2-(ih/zoom/2)':s={w}x{h},fps={fps}"
    )


def kenburns_static(w: int = 1080, h: int = 1920) -> str:
    """Static scaling without animation for photo montages."""
    return f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}"


def apply_cinematic_grade(apply: bool = True) -> str:
    """Return cinematic curves filter string (or empty string if disabled).

    Effect: lift shadows (warmer), roll-off highlights, slight teal-orange shift.
    Output: subtle film-look while preserving natural skin tones.
    """
    if not apply:
        return ""
    return CINEMATIC_CURVES


def build_xfade_concat(
    n_clips: int,
    xfade_duration: float = 0.5,
    transition: str = "fade",
    fps: int = 30,
) -> str:
    """Build ffmpeg filter_complex string for crossfade transitions between N clips.

    Args:
        n_clips: number of video inputs (0-indexed)
        xfade_duration: transition duration in seconds
        transition: ffmpeg xfade transition type (fade/dissolve/fadeblack/slideup/circleopen)
        fps: frame rate (for offset calculation)

    Returns:
        filter_complex string snippet (does not include input specification)

    Usage:
        filter_complex = build_xfade_concat(3, xfade_duration=0.5)
        # Then pipe [outv] to encode args
    """
    if n_clips < 2:
        return f"[0:v]copy[outv]"

    chains = []
    prev = "0:v"

    for i in range(1, n_clips):
        out_label = f"xf{i}" if i < n_clips - 1 else "outv"
        offset = 0  # caller sets per-clip offsets; this builds the chain structure
        chains.append(
            f"[{prev}][{i}:v]xfade=transition={transition}:"
            f"duration={xfade_duration}:offset={offset}[{out_label}]"
        )
        prev = out_label

    return ";".join(chains)
