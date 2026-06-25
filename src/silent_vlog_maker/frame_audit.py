"""
silent_vlog_maker.frame_audit — Frame extraction with description caching.

Extracts keyframes from clips and caches descriptions to avoid repeated
expensive AI or ffprobe calls on the same footage.
"""
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Optional


_CACHE_DIR = Path.home() / ".cache" / "vak_frame_audit"


def _clip_hash(clip_path: Path) -> str:
    """Stable hash of (path + mtime + size) for cache keying."""
    stat = clip_path.stat()
    key = f"{clip_path}:{stat.st_mtime}:{stat.st_size}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def extract_frame(
    clip_path: Path,
    timestamp_sec: float,
    output_path: Path,
    width: int = 540,
    height: int = 960,
) -> Path:
    """Extract a single frame from a clip at the given timestamp.

    Args:
        clip_path: source video
        timestamp_sec: time offset in seconds
        output_path: where to write the JPEG
        width / height: output dimensions (scaled to fit)

    Returns: output_path
    """
    r = subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(clip_path),
         "-ss", str(timestamp_sec),
         "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,format=yuvj420p",
         "-frames:v", "1", "-q:v", "3",
         str(output_path)],
        capture_output=True, text=True,
    )
    if r.returncode:
        raise RuntimeError(f"frame extraction failed: {r.stderr[-300:]}")
    return output_path


def extract_keyframes(
    clip_path: Path,
    n_frames: int = 4,
    output_dir: Optional[Path] = None,
    width: int = 540,
    height: int = 960,
) -> list[Path]:
    """Extract N evenly-spaced keyframes from a clip.

    Returns: list of paths to extracted JPEG frames
    """
    output_dir = output_dir or (clip_path.parent / f"_frames_{clip_path.stem}")
    output_dir.mkdir(exist_ok=True)

    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(clip_path)],
        capture_output=True, text=True,
    )
    try:
        duration = float(r.stdout.strip())
    except ValueError:
        duration = 10.0

    timestamps = [duration * (i + 1) / (n_frames + 1) for i in range(n_frames)]
    frames = []

    for i, ts in enumerate(timestamps):
        out = output_dir / f"frame_{i:02d}.jpg"
        extract_frame(clip_path, ts, out, width, height)
        frames.append(out)

    return frames


def load_description_cache(clip_path: Path) -> Optional[dict]:
    """Load cached frame descriptions for a clip. Returns None if no cache."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _CACHE_DIR / f"{_clip_hash(clip_path)}.json"
    if cache_file.exists():
        try:
            return json.loads(cache_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    return None


def save_description_cache(clip_path: Path, data: dict) -> None:
    """Save frame descriptions for a clip to local cache."""
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = _CACHE_DIR / f"{_clip_hash(clip_path)}.json"
    cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def describe_clip(
    clip_path: Path,
    n_frames: int = 4,
    descriptions: Optional[list[str]] = None,
) -> dict:
    """Store or retrieve frame descriptions for a clip.

    If descriptions are provided, they are saved to cache.
    Otherwise, returns cached data or a placeholder.

    Args:
        clip_path: path to the clip
        n_frames: number of frames (for cache schema)
        descriptions: list of description strings to cache

    Returns: cached description dict
    """
    if descriptions is not None:
        data = {
            "clip": str(clip_path),
            "n_frames": n_frames,
            "descriptions": descriptions,
        }
        save_description_cache(clip_path, data)
        return data

    cached = load_description_cache(clip_path)
    if cached:
        return cached

    return {
        "clip": str(clip_path),
        "n_frames": n_frames,
        "descriptions": [f"Frame {i + 1} of {clip_path.name}" for i in range(n_frames)],
        "cached": False,
    }
