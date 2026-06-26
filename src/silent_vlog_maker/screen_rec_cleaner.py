"""
silent_vlog_maker.screen_rec_cleaner — Automated cleanup of screen recordings.

Handles common issues with screen recordings:
- Status bar / notch regions
- Cursor removal
- Crop to content area
- Downscale for upload-friendly sizes
"""
import subprocess
from pathlib import Path
from typing import Optional


def crop_status_bar(
    input_path: Path,
    output_path: Path,
    top_crop_px: int = 40,
    bottom_crop_px: int = 0,
    left_crop_px: int = 0,
    right_crop_px: int = 0,
) -> Path:
    """Crop status bar and navigation bar regions from screen recordings.

    Args:
        input_path: source screen recording
        output_path: cropped output
        top_crop_px: pixels to remove from top (status bar)
        bottom_crop_px: pixels to remove from bottom (nav bar)
        left_crop_px / right_crop_px: side crops

    Returns: output_path
    """
    r = subprocess.run(
        ["ffprobe", "-v", "error",
         "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "csv=p=0", str(input_path)],
        capture_output=True, text=True,
    )
    try:
        w_str, h_str = r.stdout.strip().split(",")
        w, h = int(w_str), int(h_str)
    except (ValueError, IndexError):
        raise RuntimeError(f"Could not probe dimensions of {input_path}")

    crop_w = w - left_crop_px - right_crop_px
    crop_h = h - top_crop_px - bottom_crop_px
    crop_x = left_crop_px
    crop_y = top_crop_px

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-vf", f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y}",
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"crop_status_bar failed: {result.stderr[-300:]}")
    return output_path


def downscale_for_upload(
    input_path: Path,
    output_path: Path,
    max_width: int = 1920,
    max_height: int = 1080,
    crf: int = 22,
) -> Path:
    """Downscale a screen recording to upload-friendly dimensions.

    Preserves aspect ratio. Only downscales, never upscales.

    Returns: output_path
    """
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-vf", (
            f"scale='if(gt(iw,{max_width}),{max_width},iw)':"
            f"'if(gt(ih,{max_height}),{max_height},ih)'"
            f":force_original_aspect_ratio=decrease"
        ),
        "-c:v", "libx264", "-crf", str(crf), "-preset", "medium",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"downscale_for_upload failed: {result.stderr[-300:]}")
    return output_path


def remove_cursor_region(
    input_path: Path,
    output_path: Path,
    blur_regions: Optional[list[tuple[int, int, int, int]]] = None,
) -> Path:
    """Blur specified regions (e.g. cursor hotspot area) in a screen recording.

    Args:
        input_path: source recording
        output_path: output with blurred regions
        blur_regions: list of (x, y, w, h) regions to blur

    Returns: output_path
    """
    if not blur_regions:
        if str(input_path) != str(output_path):
            import shutil
            shutil.copy(str(input_path), str(output_path))
        return output_path

    vf_parts = []
    for x, y, w, h in blur_regions:
        vf_parts.append(
            f"[in]crop={w}:{h}:{x}:{y},boxblur=10:10[blurred];"
            f"[in][blurred]overlay={x}:{y}[out]"
        )

    vf = ";".join(vf_parts) if len(blur_regions) == 1 else vf_parts[0]

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-filter_complex", vf,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"remove_cursor_region failed: {result.stderr[-300:]}")
    return output_path


def clean_screen_recording(
    input_path: Path,
    output_path: Path,
    top_crop_px: int = 40,
    max_width: int = 1920,
    max_height: int = 1080,
) -> Path:
    """One-shot cleanup: crop status bar + downscale.

    Returns: output_path
    """
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tf:
        tmp = Path(tf.name)

    try:
        crop_status_bar(input_path, tmp, top_crop_px=top_crop_px)
        downscale_for_upload(tmp, output_path, max_width=max_width, max_height=max_height)
    finally:
        tmp.unlink(missing_ok=True)

    return output_path
