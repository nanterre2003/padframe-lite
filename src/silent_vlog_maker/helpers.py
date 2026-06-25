"""
silent_vlog_maker.helpers — Backward compatibility shim.

Old code that did:
    from silent_vlog_maker.helpers import audit_raw_files, Overlay, ...
still works. New code should import directly from the package root:
    from silent_vlog_maker import Overlay, audit_clip, ...

Refactored 2026-05-23: split 730-line monolith across dedicated sub-modules.
"""

from .constants import (
    TONEMAP_FILTER, YT_SHORTS_ENCODE_ARGS, ENCODE_ARGS_BY_PLATFORM,
    SAFE_ZONE, PLATFORM_DIMENSIONS, FONT_NOTO_BLACK, FONT_NOTO_BOLD,
    FONT_NOTO_REG, CINEMATIC_CURVES, COLOR_GOLD, COLOR_WHITE, COLOR_CREAM,
    BOX_DARK, BOX_SUBTLE, SUBTITLE_CENTER_Y, SUBTITLE_DETAIL_Y, COLOR_VARIETY,
)
from .audit import ClipAudit, audit_clip, audit_clips, print_audit_results
from .text_overlay import Overlay, POSITION_PRESETS, get_preset, list_presets
from .effects import kenburns_zoom_in, kenburns_pan_right, kenburns_static, apply_cinematic_grade
from .pipeline import build_filter_complex, make_keyframe_grid, load_voice_profile
from .scene_audit import Scene, cluster_into_scenes, print_scene_timeline
from .frame_audit import extract_frame, extract_keyframes, describe_clip
from .audit_report import generate_markdown_report, generate_json_report

# Alias for old name
audit_raw_files = audit_clips
