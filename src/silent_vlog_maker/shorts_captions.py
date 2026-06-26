"""
silent_vlog_maker.shorts_captions — Multi-level styled caption system for vertical video.

Three intensity levels for 1080×1920 Shorts format:
  Level 1 "clean"   — white base + cyan emphasis (teaching-focused)
  Level 2 "variety" — cream base + rotating accent palette (mainstream)
  Level 3 "pop"     — per-character color rotation + size variation (high-impact)
"""
import re
from dataclasses import dataclass, field
from typing import Optional

from .constants import SAFE_ZONE, COLOR_WHITE, COLOR_CREAM, COLOR_VARIETY


# ─────────────────────────────────────────────────────────────────────────────
# Safety zones (1080×1920)
# ─────────────────────────────────────────────────────────────────────────────

_PRIMARY_SUBTITLE_Y = 1180   # primary subtitle area
_MIN_FONT_PX = 60


# ─────────────────────────────────────────────────────────────────────────────
# Caption token
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CaptionToken:
    """A single styled run of text within a caption."""
    text: str
    color: str = COLOR_WHITE
    font_size: int = 80
    bold: bool = True
    emphasis: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Style generators
# ─────────────────────────────────────────────────────────────────────────────

_ACCENT_PALETTE_L2 = [
    "0xFFD700",  # gold
    "0x00E5FF",  # cyan
    "0xFF8C00",  # orange
    "0x32FF6B",  # lime
    "0xFF1493",  # magenta
]

_ACCENT_PALETTE_L3 = [
    "0xFFD700", "0x00E5FF", "0xFF1493",
    "0x32FF6B", "0xFF8C00", "0xFFF8E7",
]


def style_caption(
    text: str,
    level: int = 2,
    emphasis_words: Optional[set[str]] = None,
) -> list[CaptionToken]:
    """Generate color/size tokens for a caption string.

    Args:
        text: caption text
        level: 1 (clean), 2 (variety), 3 (pop)
        emphasis_words: set of words to highlight (level 1/2)

    Returns: list of CaptionToken
    """
    emphasis_words = emphasis_words or set()
    words = text.split()
    tokens: list[CaptionToken] = []

    for i, word in enumerate(words):
        is_emphasis = word in emphasis_words or word.lower() in emphasis_words

        if level == 1:
            color = "0x00E5FF" if is_emphasis else COLOR_WHITE
            size = 88 if is_emphasis else 80
        elif level == 2:
            color = _ACCENT_PALETTE_L2[i % len(_ACCENT_PALETTE_L2)] if is_emphasis else COLOR_CREAM
            size = 84 if is_emphasis else 80
        else:  # level 3
            color = _ACCENT_PALETTE_L3[i % len(_ACCENT_PALETTE_L3)]
            size = 88 if i % 3 == 0 else 80

        tokens.append(CaptionToken(
            text=word + (" " if i < len(words) - 1 else ""),
            color=color,
            font_size=max(size, _MIN_FONT_PX),
            bold=True,
            emphasis=is_emphasis,
        ))

    return tokens


def safe_caption_y(caption_height: int = 120) -> int:
    """Calculate safe overlay Y position avoiding platform UI elements.

    Args:
        caption_height: estimated rendered caption height in pixels

    Returns: Y coordinate for caption top edge (centered around primary subtitle area)
    """
    y = _PRIMARY_SUBTITLE_Y - caption_height // 2
    y = max(y, SAFE_ZONE["top"])
    y = min(y, SAFE_ZONE["bottom"] - caption_height)
    return y


def chunk_caption(
    text: str,
    max_chars: int = 20,
    min_chars: int = 5,
) -> list[str]:
    """Segment text into display chunks respecting phrase boundaries.

    Splits on punctuation and natural phrase boundaries.
    """
    if len(text) <= max_chars:
        return [text]

    separators = re.split(r"([，,。.!?！？；;])", text)
    chunks: list[str] = []
    current = ""

    for part in separators:
        candidate = current + part
        if len(candidate) > max_chars and current:
            if len(current.strip()) >= min_chars:
                chunks.append(current.strip())
            current = part
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    return chunks or [text]


def style_chunks_active(
    chunks: list[str],
    active_idx: int,
    level: int = 2,
    karaoke: bool = False,
) -> list[list[CaptionToken]]:
    """Highlight the active chunk with color/size emphasis.

    Args:
        chunks: all caption chunks from chunk_caption()
        active_idx: currently playing chunk index
        level: style level 1/2/3
        karaoke: if True, dim inactive chunks rather than hiding them

    Returns: list of token-lists (one per chunk)
    """
    result: list[list[CaptionToken]] = []
    for i, chunk in enumerate(chunks):
        if i == active_idx:
            tokens = style_caption(chunk, level=level)
        elif karaoke:
            tokens = [CaptionToken(text=chunk, color="0x888888", font_size=70, bold=False)]
        else:
            tokens = []  # hide inactive chunks unless karaoke mode
        result.append(tokens)
    return result
