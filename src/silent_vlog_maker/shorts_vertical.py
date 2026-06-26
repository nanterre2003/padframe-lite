"""
silent_vlog_maker.shorts_vertical — Portrait-mode Shorts pipeline (M96).

Creates 1080×1920 vertical short-form videos for food/travel content.
Processes silent footage with multi-colored captions and background music.
"""
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

from .constants import (
    FONT_NOTO_BOLD, FONT_NOTO_BLACK, FONT_NOTO_REG,
    ENCODE_ARGS_BY_PLATFORM, TONEMAP_FILTER,
    SUBTITLE_CENTER_Y, SUBTITLE_DETAIL_Y,
)


# ─────────────────────────────────────────────────────────────────────────────
# Color map for multi-color captions
# ─────────────────────────────────────────────────────────────────────────────

_COLOR_MAP = {
    "w": "&HFFFFFF&",   # white
    "o": "&H00A5FF&",   # orange (ASS BGR)
    "y": "&H00FFFF&",   # yellow (ASS BGR)
    "r": "&H0000FF&",   # red
    "g": "&H00FF00&",   # green
}

_EMOJI_RE = re.compile(
    "[\U00010000-\U0010ffff"
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "☀-➿"
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    return _EMOJI_RE.sub("", text).strip()


def normalize_to_portrait(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    apply_tonemap: bool = True,
) -> Path:
    """Convert phone video (.MOV) to upright 1080×1920/30fps format.

    Handles rotation metadata automatically (portrait sources rotated -90°
    from sensor get corrected without double-rotation).

    Args:
        input_path: raw footage path
        output_path: normalized output path
        width / height: target dimensions (default 1080×1920)
        fps: output frame rate
        apply_tonemap: True to convert HLG/HDR10 → SDR BT.709

    Returns: output_path as Path
    """
    vf_parts = []
    if apply_tonemap:
        vf_parts.append(TONEMAP_FILTER)

    vf_parts.append(
        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},"
        f"fps={fps}"
    )

    vf = ",".join(vf_parts)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_path),
        "-vf", vf,
        "-c:v", "libx264", "-crf", "18", "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"normalize_to_portrait failed:\n{r.stderr[-600:]}")
    return Path(output_path)


def build_multicolor_ass(
    caps: list[tuple],
    output_ass: Union[str, Path],
    font_name: str = "Noto Sans TC",
    main_font_size: int = 124,
    addr_font_size: int = 58,
    main_y: int = SUBTITLE_CENTER_Y,
    addr_y: int = SUBTITLE_DETAIL_Y,
) -> Path:
    """Generate ASS subtitle file with inline color codes.

    Args:
        caps: list of (start_s, end_s, [(text, color_code), ...], kind)
              kind: 'main' | 'addr'
              color_code: 'w' white / 'o' orange / 'y' yellow / 'r' red / 'g' green
        output_ass: path to write .ass file
        font_name: ASS font family name
        main_font_size / addr_font_size: font sizes
        main_y / addr_y: vertical positions

    Returns: output_ass as Path
    """
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,{font_name},{main_font_size},&HFFFFFF&,&H000000&,&H000000&,&H80000000&,-1,0,0,0,100,100,0,0,1,6,0,5,0,0,0,1
Style: Addr,{font_name},{addr_font_size},&HFFFFFF&,&H000000&,&H000000&,&H80000000&,-1,0,0,0,100,100,0,0,1,4,0,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = [header]

    def _fmt_time(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = sec % 60
        return f"{h}:{m:02d}:{s:05.2f}"

    for start_s, end_s, tokens, kind in caps:
        style = "Main" if kind == "main" else "Addr"
        pos_y = main_y if kind == "main" else addr_y

        text_parts = []
        for raw_text, color_key in tokens:
            text = _strip_emoji(raw_text)
            if not text:
                continue
            color = _COLOR_MAP.get(color_key, "&HFFFFFF&")
            text_parts.append(f"{{\\c{color}}}{text}{{\\c&HFFFFFF&}}")

        ass_text = "".join(text_parts)
        pos = f"{{\\an5\\pos(540,{pos_y})}}"
        line = (
            f"Dialogue: 0,{_fmt_time(start_s)},{_fmt_time(end_s)},"
            f"{style},,0,0,0,,{pos}{ass_text}"
        )
        lines.append(line)

    Path(output_ass).write_text("\n".join(lines), encoding="utf-8-sig")
    return Path(output_ass)


def find_music_highlight(bgm_path: Union[str, Path], window_sec: float = 10.0) -> float:
    """Analyze BGM using ffmpeg's ebur128 filter to find the most energetic section.

    Returns: start time in seconds of the best highlight window.
    """
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats",
         "-i", str(bgm_path),
         "-af", "ebur128=peak=true",
         "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )

    loudness_at: list[tuple[float, float]] = []
    for line in r.stderr.splitlines():
        if "t:" in line and "M:" in line:
            try:
                t = float(line.split("t:")[1].split()[0])
                m = float(line.split("M:")[1].split()[0])
                loudness_at.append((t, m))
            except (ValueError, IndexError):
                pass

    if not loudness_at:
        return 0.0

    best_start = 0.0
    best_score = float("-inf")

    for i, (t, _) in enumerate(loudness_at):
        window_end = t + window_sec
        window_vals = [m for ts, m in loudness_at if t <= ts <= window_end]
        if window_vals:
            score = sum(window_vals) / len(window_vals)
            if score > best_score:
                best_score = score
                best_start = t

    return best_start


def beat_rate(bgm_path: Union[str, Path]) -> float:
    """Calculate rhythmic density as pulse peaks per second (song energy proxy)."""
    r = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats",
         "-i", str(bgm_path),
         "-af", "astats=metadata=1:reset=1,ametadata=print:key=lavfi.astats.Overall.RMS_level",
         "-f", "null", "-"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    peaks = [line for line in r.stderr.splitlines() if "RMS_level" in line]
    dur_r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(bgm_path)],
        capture_output=True, text=True,
    )
    try:
        dur = float(dur_r.stdout.strip())
        return len(peaks) / dur if dur > 0 else 0.0
    except ValueError:
        return 0.0


def pick_bgm(
    candidates: list[Union[str, Path]],
    required_duration: float = 60.0,
    prefer_energy: bool = True,
) -> Optional[Path]:
    """Select the best background track from candidates.

    Prefers tracks with sufficient duration; optionally picks the highest energy.

    Args:
        candidates: list of audio file paths
        required_duration: minimum track duration in seconds
        prefer_energy: if True, pick highest beat_rate among qualifying tracks

    Returns: selected Path, or None if no candidates qualify
    """
    qualifying: list[tuple[Path, float]] = []

    for c in candidates:
        p = Path(c)
        if not p.exists():
            continue
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(p)],
            capture_output=True, text=True,
        )
        try:
            dur = float(r.stdout.strip())
        except ValueError:
            continue
        if dur >= required_duration:
            energy = beat_rate(p) if prefer_energy else 0.0
            qualifying.append((p, energy))

    if not qualifying:
        return None

    if prefer_energy:
        qualifying.sort(key=lambda x: -x[1])
    return qualifying[0][0]


def build_one_short(
    segs: list[tuple],
    caps: list[tuple],
    bgm: Union[str, Path],
    out: Union[str, Path],
    vol: float = 0.35,
    bgm_start: Union[float, str] = 0.0,
    platform: str = "yt_shorts",
    font_name: str = "Noto Sans TC",
) -> Path:
    """Build a complete vertical Short: concat segments + captions + BGM.

    Args:
        segs: list of (norm_video_path, trim_start_sec, trim_duration_sec)
        caps: list of (start_s, end_s, [(text, color), ...], kind)
              kind: 'main' | 'addr'
        bgm: background music file path
        out: output MP4 path
        vol: BGM volume (0.0–1.0)
        bgm_start: start time in BGM to use (float seconds, or "auto" to find highlight)
        platform: encode preset from ENCODE_ARGS_BY_PLATFORM
        font_name: ASS font family name

    Returns: output path as Path
    """
    out = Path(out)
    bgm = Path(bgm)
    work = out.parent / f"_work_{out.stem}"
    work.mkdir(exist_ok=True)

    if bgm_start == "auto":
        total_dur = sum(dur for _, _, dur in segs)
        bgm_start = find_music_highlight(bgm, window_sec=min(total_dur, 15.0))

    # Build filter_complex: concat video segments
    inputs: list[str] = []
    filter_parts: list[str] = []

    for i, (clip, start, dur) in enumerate(segs):
        inputs.extend(["-i", str(clip)])
        filter_parts.append(f"[{i}:v]trim={start}:{start + dur},setpts=PTS-STARTPTS[v{i}]")

    concat_in = "".join(f"[v{i}]" for i in range(len(segs)))
    filter_parts.append(f"{concat_in}concat=n={len(segs)}:v=1:a=0[concatv]")

    # BGM audio chain with fade + volume
    total_dur = sum(dur for _, _, dur in segs)
    bgm_idx = len(segs)
    inputs.extend(["-i", str(bgm)])

    fo_start = max(0.0, total_dur - 2.0)
    audio_chain = (
        f"[{bgm_idx}:a]atrim={bgm_start}:{bgm_start + total_dur},"
        f"asetpts=PTS-STARTPTS,"
        f"afade=t=in:st=0:d=0.3,"
        f"afade=t=out:st={fo_start}:d=2.0,"
        f"acompressor=threshold=-12dB:ratio=3:attack=5:release=100,"
        f"volume={vol}[bgma]"
    )
    filter_parts.append(audio_chain)

    # Build ASS subtitles and include the filter inside filter_complex
    ass_path = work / "captions.ass"
    build_multicolor_ass(caps, ass_path, font_name=font_name)
    ass_escaped = str(ass_path).replace(chr(92), "/").replace(":", "\\:")
    filter_parts.append(f"[concatv]ass='{ass_escaped}'[outv]")

    filter_complex = ";".join(filter_parts)

    encode_args = list(ENCODE_ARGS_BY_PLATFORM.get(platform, ENCODE_ARGS_BY_PLATFORM["yt_shorts"]))

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[bgma]",
        *encode_args,
        str(out),
    ]

    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode:
        raise RuntimeError(f"build_one_short failed:\n{r.stderr[-800:]}")

    return out


# ── Self-tests (no ffmpeg needed) ──────────────────────────────────────────

def _test_multicolor_ass():
    import tempfile, os
    caps = [
        (0.3, 5.0, [("video-autopilot-kit", "g"), ("demo", "y")], "main"),
        (5.3, 9.7, [("pure ", "w"), ("ffmpeg", "o"), (" pipeline", "w")], "main"),
        (5.3, 9.7, [("no CapCut needed", "w")], "addr"),
    ]
    with tempfile.NamedTemporaryFile(suffix=".ass", delete=False) as tf:
        path = tf.name
    try:
        result = build_multicolor_ass(caps, path)
        content = Path(result).read_text(encoding="utf-8-sig")
        assert "video-autopilot-kit" in content
        assert "\\c&H00FF00&" in content  # green
        print("✅ build_multicolor_ass self-test passed")
    finally:
        os.unlink(path)


def _test_strip_emoji():
    assert _strip_emoji("Hello 🎉 World") == "Hello  World"
    assert _strip_emoji("純文字") == "純文字"
    print("✅ _strip_emoji self-test passed")


if __name__ == "__main__":
    _test_strip_emoji()
    _test_multicolor_ass()
