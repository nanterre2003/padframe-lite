"""
silent_vlog_maker.scene_audit — Chronological scene clustering.

Clusters clips by time (30-min gaps) and location (1km radius) to
group footage into logical scenes for timeline assembly.
"""
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .audit import ClipAudit


@dataclass
class Scene:
    """A cluster of clips that belong to the same scene."""
    clips: list[ClipAudit] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location_label: str = ""
    total_duration_sec: float = 0.0


def _parse_iso6709(location: str) -> Optional[tuple[float, float]]:
    """Parse ISO 6709 location string to (lat, lon). Returns None if invalid."""
    try:
        location = location.strip().rstrip("/")
        # Format: ±DD.dddd±DDD.dddd
        import re
        m = re.match(r"([+-]\d+\.?\d*)([+-]\d+\.?\d*)", location)
        if m:
            return float(m.group(1)), float(m.group(2))
    except (ValueError, AttributeError):
        pass
    return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two GPS coordinates."""
    R = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(d_lon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def cluster_into_scenes(
    clips: list[ClipAudit],
    time_gap_min: float = 30.0,
    location_radius_km: float = 1.0,
) -> list[Scene]:
    """Cluster clips into scenes by time gap and location proximity.

    Args:
        clips: list of ClipAudit (sorted by creation_time if available)
        time_gap_min: minutes between clips to start a new scene
        location_radius_km: km radius for same-location grouping

    Returns: list of Scene groups
    """
    if not clips:
        return []

    def _parse_time(ct: str) -> Optional[datetime]:
        if not ct:
            return None
        try:
            return datetime.fromisoformat(ct.replace("Z", "+00:00"))
        except ValueError:
            return None

    sorted_clips = sorted(clips, key=lambda c: c.creation_time or "")
    scenes: list[Scene] = []
    current_scene = Scene(clips=[sorted_clips[0]])
    current_scene.start_time = _parse_time(sorted_clips[0].creation_time)
    current_scene.total_duration_sec = sorted_clips[0].duration_sec

    for clip in sorted_clips[1:]:
        clip_time = _parse_time(clip.creation_time)
        prev_time = _parse_time(current_scene.clips[-1].creation_time)

        time_break = False
        if clip_time and prev_time:
            gap_min = (clip_time - prev_time).total_seconds() / 60
            time_break = gap_min > time_gap_min

        if time_break:
            current_scene.end_time = _parse_time(current_scene.clips[-1].creation_time)
            scenes.append(current_scene)
            current_scene = Scene(clips=[clip])
            current_scene.start_time = clip_time
            current_scene.total_duration_sec = clip.duration_sec
        else:
            current_scene.clips.append(clip)
            current_scene.total_duration_sec += clip.duration_sec

    current_scene.end_time = _parse_time(current_scene.clips[-1].creation_time)
    scenes.append(current_scene)

    return scenes


def print_scene_timeline(scenes: list[Scene]) -> None:
    """Print a chronological scene timeline."""
    print("=" * 60)
    print(f"Scene Timeline — {len(scenes)} scene(s)")
    print("=" * 60)
    for i, scene in enumerate(scenes):
        start = scene.start_time.strftime("%H:%M") if scene.start_time else "?"
        end = scene.end_time.strftime("%H:%M") if scene.end_time else "?"
        n = len(scene.clips)
        dur = scene.total_duration_sec
        print(f"\nScene {i + 1}: {start}–{end} | {n} clip(s) | {dur:.1f}s total")
        if scene.location_label:
            print(f"  Location: {scene.location_label}")
        for clip in scene.clips:
            print(f"  {clip.path.name} ({clip.duration_sec:.1f}s)")
