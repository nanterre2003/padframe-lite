"""
silent_vlog_maker.shorts_template — Template system for Shorts production.

Provides reusable production templates (intro, mid-cut, outro) so each
video follows the same structure without manual re-configuration.
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .constants import (
    COLOR_GOLD, COLOR_WHITE, COLOR_CREAM,
    SUBTITLE_CENTER_Y, SUBTITLE_DETAIL_Y,
)
from .text_overlay import Overlay


@dataclass
class ShortsTemplate:
    """Production template for a single vertical Short.

    Defines the caption structure, overlay timing, and BGM settings
    for a standardized video format (food / travel / lifestyle).
    """
    name: str
    format: str = "9:16"            # aspect ratio
    max_duration_sec: float = 59.0  # YouTube Shorts max
    main_font_size: int = 80
    addr_font_size: int = 52
    main_y: int = SUBTITLE_CENTER_Y
    addr_y: int = SUBTITLE_DETAIL_Y
    bgm_volume: float = 0.35
    intro_duration_sec: float = 1.0
    outro_pad_sec: float = 0.5
    platform: str = "yt_shorts"


# ── Preset templates ──────────────────────────────────────────────────────────

FOOD_VLOG_TEMPLATE = ShortsTemplate(
    name="food_vlog",
    max_duration_sec=59.0,
    main_font_size=82,
    addr_font_size=52,
    bgm_volume=0.30,
    intro_duration_sec=0.8,
    outro_pad_sec=1.0,
)

TRAVEL_TEMPLATE = ShortsTemplate(
    name="travel",
    max_duration_sec=59.0,
    main_font_size=78,
    addr_font_size=50,
    bgm_volume=0.35,
    intro_duration_sec=1.2,
    outro_pad_sec=1.5,
)

LIFESTYLE_TEMPLATE = ShortsTemplate(
    name="lifestyle",
    max_duration_sec=59.0,
    main_font_size=76,
    addr_font_size=50,
    bgm_volume=0.32,
    intro_duration_sec=1.0,
    outro_pad_sec=1.0,
)

TEMPLATE_REGISTRY: dict[str, ShortsTemplate] = {
    "food_vlog": FOOD_VLOG_TEMPLATE,
    "travel": TRAVEL_TEMPLATE,
    "lifestyle": LIFESTYLE_TEMPLATE,
}


def get_template(name: str) -> ShortsTemplate:
    """Get a production template by name.

    Raises KeyError if template not found.
    """
    if name not in TEMPLATE_REGISTRY:
        raise KeyError(f"Template '{name}' not found. Available: {list(TEMPLATE_REGISTRY.keys())}")
    return TEMPLATE_REGISTRY[name]


def list_templates() -> list[str]:
    """List all available template names."""
    return list(TEMPLATE_REGISTRY.keys())


@dataclass
class ShortsBuildPlan:
    """A fully-specified production plan for building one Short."""
    template: ShortsTemplate
    clips: list[tuple[str, float, float]] = field(default_factory=list)
    captions: list[tuple] = field(default_factory=list)
    bgm_path: Optional[Path] = None
    bgm_start: float = 0.0
    output_path: Optional[Path] = None
    outro_title: Optional[str] = None
    outro_address: Optional[str] = None


def build_plan(
    template_name: str,
    clips: list[tuple],
    captions: list[tuple],
    bgm_path: Path,
    output_path: Path,
    bgm_start: float = 0.0,
    outro_title: Optional[str] = None,
    outro_address: Optional[str] = None,
) -> ShortsBuildPlan:
    """Construct a ShortsBuildPlan from named template + production inputs.

    Args:
        template_name: name of template to use
        clips: list of (norm_path, trim_start, trim_dur)
        captions: list of (start_s, end_s, [(text, color)], kind)
        bgm_path: path to background music
        output_path: output MP4 destination
        bgm_start: BGM start time in seconds
        outro_title / outro_address: optional M56 outro card content

    Returns: ShortsBuildPlan
    """
    template = get_template(template_name)
    return ShortsBuildPlan(
        template=template,
        clips=clips,
        captions=captions,
        bgm_path=bgm_path,
        bgm_start=bgm_start,
        output_path=output_path,
        outro_title=outro_title,
        outro_address=outro_address,
    )
