"""
silent_vlog_maker.text_overlay — Text overlay builder for ffmpeg drawtext filters.
"""
from dataclasses import dataclass, field
from typing import Optional

from .constants import (
    FONT_NOTO_BOLD, FONT_NOTO_BLACK, FONT_NOTO_REG,
    COLOR_GOLD, COLOR_WHITE, COLOR_CREAM,
    BOX_DARK, BOX_SUBTLE,
    SUBTITLE_CENTER_Y, SUBTITLE_DETAIL_Y,
)


@dataclass
class Overlay:
    """Single drawtext overlay spec. Position presets handle safe zone."""
    text: str
    position: str                  # preset name OR raw "x=N:y=N" string
    t_start: float = 0.0
    t_end: float = 5.0
    fade_in: float = 0.4
    fade_out: float = 0.5
    font: str = FONT_NOTO_BOLD
    font_size: int = 56
    font_color: str = COLOR_WHITE
    border_color: str = "black"
    border_width: int = 3
    box: bool = True
    box_color: str = BOX_SUBTLE
    box_border_w: int = 14

    def to_drawtext(self, text_file_path: str) -> str:
        """Convert to ffmpeg drawtext filter string (without leading comma)."""
        alpha_expr = (
            f"if(lt(t,{self.t_start}),0,"
            f"if(lt(t,{self.t_start + self.fade_in}),"
            f"(t-{self.t_start})/{self.fade_in},"
            f"if(gt(t,{self.t_end - self.fade_out}),"
            f"({self.t_end}-t)/{self.fade_out},1)))"
        )
        enable_expr = f"between(t,{self.t_start},{self.t_end})"

        pos = _resolve_position(self.position)
        box_str = f":box=1:boxcolor={self.box_color}:boxborderw={self.box_border_w}" if self.box else ""

        return (
            f"drawtext=fontfile='{self.font}':textfile='{text_file_path}':"
            f"fontsize={self.font_size}:fontcolor={self.font_color}:"
            f"borderw={self.border_width}:bordercolor={self.border_color}@0.8"
            f"{box_str}:{pos}:"
            f"alpha='{alpha_expr}':enable='{enable_expr}'"
        )


def _resolve_position(position: str) -> str:
    """Resolve a preset name or passthrough a raw x=N:y=N string."""
    all_presets = {}
    for family in LAYOUT_PRESETS.values():
        all_presets.update(family)
    if position in all_presets:
        p = all_presets[position]
        return f"x={p['x']}:y={p['y']}"
    return position  # assume already formatted as "x=N:y=N"


# ─────────────────────────────────────────────────────────────────────
# Portrait presets (1080×1920 Shorts)
# ─────────────────────────────────────────────────────────────────────

POSITION_PRESETS: dict[str, dict] = {
    "title_hook": {
        "x": "(w-tw)/2", "y": str(SUBTITLE_CENTER_Y),
        "font_size": 80, "font_color": COLOR_GOLD,
        "box_color": BOX_DARK, "box_border_w": 20,
    },
    "title_detail": {
        "x": "(w-tw)/2", "y": str(SUBTITLE_DETAIL_Y),
        "font_size": 56, "font_color": COLOR_CREAM,
        "box_color": BOX_SUBTLE, "box_border_w": 14,
    },
    # Legacy presets
    "main_title": {
        "x": "(w-tw)/2", "y": str(SUBTITLE_CENTER_Y),
        "font_size": 72, "font_color": COLOR_GOLD,
    },
    "subtitle": {
        "x": "(w-tw)/2", "y": str(SUBTITLE_DETAIL_Y),
        "font_size": 52, "font_color": COLOR_WHITE,
    },
    "lower_third": {
        "x": "(w-tw)/2", "y": "h-300",
        "font_size": 48, "font_color": COLOR_WHITE,
    },
    "top_banner": {
        "x": "(w-tw)/2", "y": "280",
        "font_size": 56, "font_color": COLOR_GOLD,
    },
}


# ─────────────────────────────────────────────────────────────────────
# Landscape presets (1920×1080)
# ─────────────────────────────────────────────────────────────────────

LANDSCAPE_PRESETS: dict[str, dict] = {
    "title_hook": {
        "x": "(w-tw)/2", "y": "800",
        "font_size": 64, "font_color": COLOR_GOLD,
        "box_color": BOX_DARK, "box_border_w": 18,
    },
    "title_detail": {
        "x": "(w-tw)/2", "y": "900",
        "font_size": 44, "font_color": COLOR_CREAM,
        "box_color": BOX_SUBTLE, "box_border_w": 12,
    },
    "timestamp_corner": {
        "x": "60", "y": "60",
        "font_size": 36, "font_color": COLOR_WHITE,
    },
    "location_lower_third": {
        "x": "60", "y": "h-180",
        "font_size": 44, "font_color": COLOR_WHITE,
    },
}


# ─────────────────────────────────────────────────────────────────────
# TV variety presets (landscape entertainment style)
# ─────────────────────────────────────────────────────────────────────

TV_VARIETY_PRESETS: dict[str, dict] = {
    "day_marker": {
        "x": "(w-tw)/2", "y": "(h-th)/2",
        "font_size": 110, "font_color": COLOR_GOLD,
        "box_color": "black@0.6", "box_border_w": 30,
    },
    "tv_hook": {
        "x": "(w-tw)/2", "y": "700",
        "font_size": 72, "font_color": "0x00E5FF",
        "box_color": BOX_DARK, "box_border_w": 20,
    },
    "tv_emphasis": {
        "x": "(w-tw)/2", "y": "820",
        "font_size": 80, "font_color": "0xFF1493",
        "box_color": BOX_DARK, "box_border_w": 22,
    },
}


LAYOUT_PRESETS: dict[str, dict] = {
    "portrait": POSITION_PRESETS,
    "landscape": LANDSCAPE_PRESETS,
    "landscape_variety": TV_VARIETY_PRESETS,
}


def get_preset(name: str, layout: str = "portrait") -> dict:
    """Get preset dict by name with layout dispatch."""
    family = LAYOUT_PRESETS.get(layout, POSITION_PRESETS)
    if name not in family:
        raise KeyError(f"Preset '{name}' not found in layout '{layout}'. "
                       f"Available: {list(family.keys())}")
    return family[name]


def list_presets(layout: Optional[str] = None) -> dict[str, list[str]]:
    """List all preset names per layout family."""
    if layout:
        family = LAYOUT_PRESETS.get(layout, {})
        return {layout: list(family.keys())}
    return {k: list(v.keys()) for k, v in LAYOUT_PRESETS.items()}


def make_overlay(
    text: str,
    position: str,
    t_start: float,
    t_end: float,
    layout: str = "portrait",
    **kwargs,
) -> Overlay:
    """Convenience constructor that merges preset defaults with caller overrides."""
    try:
        preset = get_preset(position, layout)
    except KeyError:
        preset = {}

    merged = {
        "font_size": preset.get("font_size", 56),
        "font_color": preset.get("font_color", COLOR_WHITE),
        "box_color": preset.get("box_color", BOX_SUBTLE),
        "box_border_w": preset.get("box_border_w", 14),
    }
    merged.update(kwargs)

    return Overlay(
        text=text,
        position=position,
        t_start=t_start,
        t_end=t_end,
        **merged,
    )
