"""
capcut_helpers.text_style — Text preset styling for CapCut drafts.

Applies preset styles to text materials in the draft JSON, replacing
manual "花字" (text flower effects) configuration.
"""
import json
import re
from pathlib import Path
from typing import Optional

from .paths import CAPCUT_USER_DATA

# ── Font cache paths ──────────────────────────────────────────────────────────
# 剪映团子 font lives in the effect cache
_APPS_DIR = Path.home() / "AppData" / "Local" / "CapCut" / "Apps"

CAPCUT_FONTS: dict[str, str] = {
    "团子": str(CAPCUT_USER_DATA / "Resources" / "Font" / "团子" / "团子.ttf"),
    "SystemFont": str(_APPS_DIR / "CapCut" / "SystemFont" / "SystemFont.ttf"),
}

# ── Preset style definitions ──────────────────────────────────────────────────

_PRESETS: dict[str, dict] = {
    "white_outline_black": {
        "font_color": "#FFFFFF",
        "border_color": "#000000",
        "border_width": 6,
        "background_color": "",
        "background_alpha": 0,
        "bold": True,
        "italic": False,
        "font_size": 60,
    },
    "white_plain": {
        "font_color": "#FFFFFF",
        "border_color": "",
        "border_width": 0,
        "background_color": "",
        "background_alpha": 0,
        "bold": False,
        "italic": False,
        "font_size": 56,
    },
    "yellow_highlight_black": {
        "font_color": "#FFD700",
        "border_color": "#000000",
        "border_width": 5,
        "background_color": "#000000",
        "background_alpha": 0.6,
        "bold": True,
        "italic": False,
        "font_size": 64,
    },
    "red_outline_black": {
        "font_color": "#FF3333",
        "border_color": "#000000",
        "border_width": 6,
        "background_color": "",
        "background_alpha": 0,
        "bold": True,
        "italic": False,
        "font_size": 62,
    },
    "teaching_primary": {
        "font_color": "#FFFFFF",
        "border_color": "#1A1A1A",
        "border_width": 4,
        "background_color": "#1A1A1A",
        "background_alpha": 0.55,
        "bold": True,
        "italic": False,
        "font_size": 58,
    },
    "teaching_secondary": {
        "font_color": "#CCCCCC",
        "border_color": "#111111",
        "border_width": 3,
        "background_color": "#111111",
        "background_alpha": 0.45,
        "bold": False,
        "italic": False,
        "font_size": 48,
    },
}


def _is_chinese_text(text: str) -> bool:
    """Detect CJK characters for dual-tier formatting decisions."""
    return bool(re.search(r"[一-鿿぀-ヿ㐀-䶿]", text))


def _build_style_entry(preset: dict) -> dict:
    """Convert a preset dict to CapCut style array entry format."""
    entry: dict = {
        "bold": preset.get("bold", False),
        "italic": preset.get("italic", False),
        "size": preset.get("font_size", 56),
        "fill_color": preset.get("font_color", "#FFFFFF"),
    }
    if preset.get("border_color"):
        entry["border_color"] = preset["border_color"]
        entry["border_width"] = preset.get("border_width", 0)
    if preset.get("background_color"):
        entry["background_color"] = preset["background_color"]
        entry["background_alpha"] = preset.get("background_alpha", 0.5)
    return entry


def apply_text_preset(
    text_material: dict,
    preset_name: str,
) -> dict:
    """Apply a named preset to a single text material dict.

    Modifies `text_material` in-place and returns it.
    """
    if preset_name not in _PRESETS:
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {list(_PRESETS)}")

    preset = _PRESETS[preset_name]
    try:
        co = json.loads(text_material.get("content", "{}"))
    except json.JSONDecodeError:
        co = {}

    text = co.get("text", "")
    text_len = len(text)

    style_entry = _build_style_entry(preset)
    style_entry["range"] = [0, text_len]

    co["styles"] = [style_entry]
    text_material["content"] = json.dumps(co, ensure_ascii=False, separators=(",", ":"))
    return text_material


def apply_text_preset_to_all(
    draft: dict,
    preset_name: str,
    skip_texts: Optional[set[str]] = None,
) -> int:
    """Apply a preset to all text materials in the draft.

    Args:
        draft: full draft dict
        preset_name: key from _PRESETS
        skip_texts: set of text strings to skip

    Returns: number of materials patched
    """
    skip_texts = skip_texts or set()
    texts = draft.get("materials", {}).get("texts", [])
    n = 0
    for t in texts:
        try:
            co = json.loads(t.get("content", "{}"))
            text = co.get("text", "")
        except json.JSONDecodeError:
            continue
        if not text or text in skip_texts:
            continue
        apply_text_preset(t, preset_name)
        n += 1
    return n


def apply_teaching_dual_tier(
    draft: dict,
    chinese_preset: str = "teaching_primary",
    english_preset: str = "teaching_secondary",
) -> dict[str, int]:
    """Auto-detect language per caption and apply dual-tier styling.

    Chinese text → `chinese_preset` (softer, semi-transparent bg, rounded corners)
    English/code text → `english_preset` (sharper formatting)

    Returns: {'chinese': N, 'english': N}
    """
    texts = draft.get("materials", {}).get("texts", [])
    counts = {"chinese": 0, "english": 0}

    for t in texts:
        try:
            co = json.loads(t.get("content", "{}"))
            text = co.get("text", "")
        except json.JSONDecodeError:
            continue
        if not text:
            continue

        if _is_chinese_text(text):
            apply_text_preset(t, chinese_preset)
            counts["chinese"] += 1
        else:
            apply_text_preset(t, english_preset)
            counts["english"] += 1

    return counts
