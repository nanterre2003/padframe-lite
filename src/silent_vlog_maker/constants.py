from pathlib import Path
"""
silent_vlog_maker.constants — Shared constants for R10-R21 rules.

All other modules import from this. No logic, only data.
"""

# ─────────────────────────────────────────────────────────────────────
# R12: Safe Zone (2026 YT/Shorts spec)
# ─────────────────────────────────────────────────────────────────────

SAFE_ZONE = {
    "top": 260,        # text y ≥ 260 (status bar + camera notch)
    "bottom": 1660,    # text y ≤ 1660 (description + subscribe button)
    "right": 930,      # text x ≤ 930 (like/comment/share + add-to-playlist 2026)
}


# ─────────────────────────────────────────────────────────────────────
# R10: HDR HLG/HDR10 → SDR BT.709 (tonemap=hable, npl=250 for iPhone HLG)
# ─────────────────────────────────────────────────────────────────────

TONEMAP_FILTER = (
    "zscale=t=linear:npl=250,"
    "format=gbrpf32le,"
    "zscale=p=bt709,"
    "tonemap=tonemap=hable:desat=0,"
    "zscale=t=bt709:m=bt709:r=tv,"
    "format=yuv420p"
)


# ─────────────────────────────────────────────────────────────────────
# R11 v2: Platform-aware export configs (2026-05-24 — mass production ready)
# ─────────────────────────────────────────────────────────────────────

ENCODE_ARGS_BY_PLATFORM = {
    "yt_shorts": [
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
    ],
    "yt_longform": [
        "-c:v", "libx264", "-preset", "fast", "-crf", "16",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
    ],
    "ig_reels": [
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
    ],
    "tiktok": [
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-movflags", "+faststart",
    ],
    "threads": [
        "-c:v", "libx264", "-preset", "fast", "-crf", "22",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart",
    ],
    # GPU variants — use when h264_nvenc is available
    "yt_shorts_nvenc": [
        "-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr",
        "-b:v", "8M", "-maxrate", "12M", "-bufsize", "16M",
        "-profile:v", "high", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
        "-movflags", "+faststart",
    ],
}

# Backward compat alias (used by build_filter_complex / older scripts)
YT_SHORTS_ENCODE_ARGS = ENCODE_ARGS_BY_PLATFORM["yt_shorts"]


# Platform display dimensions (informational — for filter pre-scaling decision)
PLATFORM_DIMENSIONS = {
    "yt_shorts": (1080, 1920),
    "yt_longform": (1920, 1080),
    "ig_reels": (1080, 1920),
    "tiktok": (1080, 1920),
    "threads_portrait": (1080, 1920),
    "threads_square": (1080, 1080),
}


def encode_args_for(platform: str = "yt_shorts") -> list[str]:
    """Get ffmpeg encode args for a target platform.

    Raises KeyError if platform unknown. Use `list(ENCODE_ARGS_BY_PLATFORM.keys())` to enumerate.
    """
    if platform not in ENCODE_ARGS_BY_PLATFORM:
        raise KeyError(f"Unknown platform '{platform}'. Available: {list(ENCODE_ARGS_BY_PLATFORM.keys())}")
    return list(ENCODE_ARGS_BY_PLATFORM[platform])


# ─────────────────────────────────────────────────────────────────────
# R17: Fonts — Noto Sans TC (Google 思源黑體)
# ─────────────────────────────────────────────────────────────────────

FONT_NOTO_BLACK = "C\\:/Windows/Fonts/NotoSansTC-Black.otf"
FONT_NOTO_BOLD = "C\\:/Windows/Fonts/NotoSansTC-Bold.otf"
FONT_NOTO_REG = "C\\:/Windows/Fonts/NotoSansTC-Regular.otf"

# Vlog narrative 首選 serif
FONT_NOTO_SERIF_BOLD = "assets/fonts/NotoSerifCJK-Bold.ttc"

# Legacy fonts (kept for backward compat)
FONT_BOLD = "C\\:/Windows/Fonts/msjhbd.ttc"
FONT_REG = "C\\:/Windows/Fonts/msjh.ttc"


# ─────────────────────────────────────────────────────────────────────
# R17: Cinematic Color Grade — ffmpeg curves film-look
# ─────────────────────────────────────────────────────────────────────

CINEMATIC_CURVES = (
    "curves=master='0/0 0.25/0.22 0.5/0.5 0.75/0.78 1/1':"
    "red='0/0 0.5/0.52 1/0.98':"
    "blue='0/0.02 0.5/0.48 1/1':"
    "green='0/0 0.5/0.5 1/1',"
    "eq=saturation=0.95:contrast=1.05"
)


# ─────────────────────────────────────────────────────────────────────
# R12 + R17: Typography color palette
# ─────────────────────────────────────────────────────────────────────

COLOR_GOLD = "0xFFD700"
COLOR_WHITE = "white"
COLOR_CREAM = "0xFFF8E7"
BOX_DARK = "black@0.55"
BOX_SUBTLE = "black@0.5"
BOX_CINEMATIC = "black@0.6"


# ─────────────────────────────────────────────────────────────────────
# R19 + M5: Unified center-bottom subtitle position (Shorts portrait)
# ─────────────────────────────────────────────────────────────────────

SUBTITLE_CENTER_Y = 1280
SUBTITLE_DETAIL_Y = 1400


# ─────────────────────────────────────────────────────────────────────
# R21 + M15: 綜藝字卡 vibrant color palette (landscape long-form)
# ─────────────────────────────────────────────────────────────────────

COLOR_VARIETY = {
    "gold": "0xFFD700",
    "cyan": "0x00E5FF",
    "magenta": "0xFF1493",
    "lime": "0x32FF6B",
    "orange": "0xFF8C00",
    "white": "white",
    "cream": "0xFFF8E7",
}
