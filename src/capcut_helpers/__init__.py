"""
capcut_helpers — CapCut Desktop JSON automation toolkit (v1, 2026-05-24).

Abstracts repetitive CapCut Desktop JSON manipulation into reusable helpers:
process management, draft I/O, muting, effects, text styling, post-export
processing, subtitle corrections, b-roll matching, and delivery QA.
"""

from .paths import (
    draft_path,
    draft_files,
    discover_all_draft_jsons,
    CAPCUT_USER_DATA,
    DRAFTS_ROOT,
    PROJECT_ROOT,
)
from .process import kill_capcut_all, is_capcut_running, safe_kill_then_verify
from .draft_io import (
    load_draft,
    save_draft_with_sync,
    set_canvas_portrait,
    set_canvas_landscape,
    auto_set_canvas,
    verify_sync,
)
from .mute import mute_all_video_segments, mute_specific_segments, audit_mute_state
from .effects import (
    find_effect_material,
    get_effect_cache_path,
    apply_effect_to_all_captions,
    swap_effect,
    apply_effect_to_segment,
    count_effects_by_id,
)
from .audit import audit_draft, print_audit_report
from .text_style import (
    apply_text_preset,
    apply_text_preset_to_all,
    apply_teaching_dual_tier,
)
from .subtitle_corrections import (
    apply_subtitle_corrections,
    scan_potential_errors,
    BRAND_CORRECTIONS,
)
from .caption_broll_matcher import (
    score_broll_for_caption,
    match_brolls_to_captions,
    audit_caption_broll_mismatch,
    auto_sequence_brolls,
    print_mismatch_report,
    print_sequence_plan,
    BrollAssignment,
    EXAMPLE_KEYWORD_MAP,
)
from .broll_audit import audit_broll_ratio, audit_narration_sync, print_broll_audit
from .delivery_qa import run_full_qa, print_qa_report
from .invariants import validate_invariants, TEXT_MATERIAL_INVARIANTS, TEXT_MATERIAL_AUTO_FIX
from .post_export import (
    force_mix_bgm,
    add_outro_card,
    detect_voice_end,
    reencode_player_safe,
    trim_to_voice_end,
    finalize_export,
)

__all__ = [
    # paths
    "draft_path", "draft_files", "discover_all_draft_jsons",
    "CAPCUT_USER_DATA", "DRAFTS_ROOT", "PROJECT_ROOT",
    # process
    "kill_capcut_all", "is_capcut_running", "safe_kill_then_verify",
    # draft_io
    "load_draft", "save_draft_with_sync",
    "set_canvas_portrait", "set_canvas_landscape", "auto_set_canvas", "verify_sync",
    # mute
    "mute_all_video_segments", "mute_specific_segments", "audit_mute_state",
    # effects
    "find_effect_material", "get_effect_cache_path",
    "apply_effect_to_all_captions", "swap_effect",
    "apply_effect_to_segment", "count_effects_by_id",
    # audit
    "audit_draft", "print_audit_report",
    # text_style
    "apply_text_preset", "apply_text_preset_to_all", "apply_teaching_dual_tier",
    # subtitle_corrections
    "apply_subtitle_corrections", "scan_potential_errors", "BRAND_CORRECTIONS",
    # caption_broll_matcher
    "score_broll_for_caption", "match_brolls_to_captions",
    "audit_caption_broll_mismatch", "auto_sequence_brolls",
    "print_mismatch_report", "print_sequence_plan",
    "BrollAssignment", "EXAMPLE_KEYWORD_MAP",
    # broll_audit
    "audit_broll_ratio", "audit_narration_sync", "print_broll_audit",
    # delivery_qa
    "run_full_qa", "print_qa_report",
    # invariants
    "validate_invariants", "TEXT_MATERIAL_INVARIANTS", "TEXT_MATERIAL_AUTO_FIX",
    # post_export
    "force_mix_bgm", "add_outro_card", "detect_voice_end",
    "reencode_player_safe", "trim_to_voice_end", "finalize_export",
]
