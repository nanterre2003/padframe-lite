"""
silent_vlog_maker — FFmpeg-only pipeline for silent vlogs and short-form content (v3, 2026-05-24).

Main entry points:
  normalize_to_portrait()  — convert phone footage to 1080×1920 / 30fps
  build_one_short()        — full pipeline: concat + captions + BGM → final MP4

Also exposes all audit, scene, frame, effects, and overlay utilities.
"""

from .shorts_vertical import normalize_to_portrait, build_one_short, build_multicolor_ass
from .constants import (
    TONEMAP_FILTER, ENCODE_ARGS_BY_PLATFORM, YT_SHORTS_ENCODE_ARGS,
    SAFE_ZONE, PLATFORM_DIMENSIONS, FONT_NOTO_BLACK, FONT_NOTO_BOLD,
    FONT_NOTO_REG, CINEMATIC_CURVES, COLOR_GOLD, COLOR_WHITE, COLOR_CREAM,
    BOX_DARK, BOX_SUBTLE, SUBTITLE_CENTER_Y, SUBTITLE_DETAIL_Y, COLOR_VARIETY,
    encode_args_for,
)
from .text_overlay import (
    Overlay, POSITION_PRESETS, LANDSCAPE_PRESETS, TV_VARIETY_PRESETS,
    LAYOUT_PRESETS, get_preset, list_presets, make_overlay,
)
from .effects import (
    kenburns_zoom_in, kenburns_pan_right, kenburns_static,
    apply_cinematic_grade, build_xfade_concat,
)
from .pipeline import build_filter_complex, make_keyframe_grid, load_voice_profile
from .audit import ClipAudit, audit_clip, audit_clips, print_audit_results
from .scene_audit import Scene, cluster_into_scenes, print_scene_timeline
from .frame_audit import extract_frame, extract_keyframes, describe_clip
from .audit_report import generate_markdown_report, generate_json_report
from .asset_scanner import (
    scan_bgm, scan_fonts, scan_templates, scan_footage, inventory_project, print_inventory,
)
from .quality_check import verify_output, print_quality_check
from .shorts_captions import CaptionToken, style_caption, safe_caption_y, chunk_caption
from .shorts_template import (
    ShortsTemplate, ShortsBuildPlan, get_template, list_templates, build_plan,
    FOOD_VLOG_TEMPLATE, TRAVEL_TEMPLATE, LIFESTYLE_TEMPLATE,
)

__all__ = [
    # core pipeline
    "normalize_to_portrait", "build_one_short", "build_multicolor_ass",
    # constants
    "TONEMAP_FILTER", "ENCODE_ARGS_BY_PLATFORM", "YT_SHORTS_ENCODE_ARGS",
    "SAFE_ZONE", "PLATFORM_DIMENSIONS", "encode_args_for",
    "FONT_NOTO_BLACK", "FONT_NOTO_BOLD", "FONT_NOTO_REG",
    "CINEMATIC_CURVES", "COLOR_GOLD", "COLOR_WHITE", "COLOR_CREAM",
    "BOX_DARK", "BOX_SUBTLE", "SUBTITLE_CENTER_Y", "SUBTITLE_DETAIL_Y", "COLOR_VARIETY",
    # text_overlay
    "Overlay", "POSITION_PRESETS", "LANDSCAPE_PRESETS", "TV_VARIETY_PRESETS",
    "LAYOUT_PRESETS", "get_preset", "list_presets", "make_overlay",
    # effects
    "kenburns_zoom_in", "kenburns_pan_right", "kenburns_static",
    "apply_cinematic_grade", "build_xfade_concat",
    # pipeline
    "build_filter_complex", "make_keyframe_grid", "load_voice_profile",
    # audit
    "ClipAudit", "audit_clip", "audit_clips", "print_audit_results",
    # scene_audit
    "Scene", "cluster_into_scenes", "print_scene_timeline",
    # frame_audit
    "extract_frame", "extract_keyframes", "describe_clip",
    # reports
    "generate_markdown_report", "generate_json_report",
    # asset_scanner
    "scan_bgm", "scan_fonts", "scan_templates", "scan_footage",
    "inventory_project", "print_inventory",
    # quality_check
    "verify_output", "print_quality_check",
    # shorts_captions
    "CaptionToken", "style_caption", "safe_caption_y", "chunk_caption",
    # shorts_template
    "ShortsTemplate", "ShortsBuildPlan", "get_template", "list_templates", "build_plan",
    "FOOD_VLOG_TEMPLATE", "TRAVEL_TEMPLATE", "LIFESTYLE_TEMPLATE",
]
