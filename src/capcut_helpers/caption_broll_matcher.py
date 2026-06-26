"""
capcut_helpers.caption_broll_matcher — AP15 (2026-05-26).

Zero-config caption-to-b-roll matching: name your clips after their content
(coffee.mp4 / sunset.mov / ramen.mp4) and the matcher aligns each caption to
the best-matching clip by shared words — no keyword map needed.

For non-matching captions, falls back to filler so the timeline has no gaps.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Example keyword map (override with your own for domain-specific matching)
# ─────────────────────────────────────────────────────────────────────────────

EXAMPLE_KEYWORD_MAP: dict[str, list[str]] = {
    "coffee.mp4":  ["coffee", "latte", "espresso", "cafe", "brew", "咖啡"],
    "sunset.mov":  ["sunset", "golden", "hour", "sky", "dusk", "日落", "黃昏"],
    "ramen.mp4":   ["ramen", "noodle", "soup", "bowl", "拉麵", "麵"],
    "street.mp4":  ["street", "walk", "city", "people", "路", "街"],
}


# ─────────────────────────────────────────────────────────────────────────────
# Scoring helpers
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> set[str]:
    """Lowercase, split on non-alphanumeric, return set of tokens (min length 2)."""
    tokens = re.findall(r"[a-z一-鿿]{2,}", text.lower())
    return set(tokens)


def _stem(token: str) -> str:
    """Very light stemmer: strip common English suffixes."""
    for suffix in ("ing", "ed", "er", "s", "ly"):
        if token.endswith(suffix) and len(token) > len(suffix) + 2:
            return token[: -len(suffix)]
    return token


def score_broll_for_caption(
    caption_text: str,
    broll_id: str,
    keyword_map: Optional[dict[str, list[str]]] = None,
) -> float:
    """Score how well a b-roll clip matches a caption.

    Scoring strategy:
    1. If keyword_map provided: count keyword hits (weighted higher)
    2. Always: count filename token hits vs caption tokens (fallback / supplement)

    Returns: float score (higher = better match)
    """
    cap_tokens = _tokenize(caption_text)
    cap_stems = {_stem(t) for t in cap_tokens}

    score = 0.0

    # 1. Keyword map hits (weight 2.0 each)
    if keyword_map and broll_id in keyword_map:
        for kw in keyword_map[broll_id]:
            kw_tokens = _tokenize(kw)
            if kw_tokens & cap_tokens:
                score += 2.0
            elif {_stem(t) for t in kw_tokens} & cap_stems:
                score += 1.0

    # 2. Filename token hits (weight 1.0 each)
    fname_tokens = _tokenize(Path(broll_id).stem)
    fname_stems = {_stem(t) for t in fname_tokens}

    hits = fname_tokens & cap_tokens
    stem_hits = fname_stems & cap_stems

    score += len(hits) * 1.0
    score += len(stem_hits - hits) * 0.5  # partial stem match bonus

    return score


def match_brolls_to_captions(
    captions: list[dict],
    brolls: list[dict],
    keyword_map: Optional[dict[str, list[str]]] = None,
) -> list[dict]:
    """Match each caption to the best-scoring b-roll clip.

    Args:
        captions: list of {text, start_us, duration_us}
        brolls: list of {id, source_duration_us}
        keyword_map: optional {broll_id: [keyword, ...]} for domain-specific boost

    Returns:
        list of {caption_idx, caption_text, broll_id, score, fallback}
    """
    results = []
    for i, cap in enumerate(captions):
        text = cap.get("text", "")
        best_id = None
        best_score = -1.0
        for broll in brolls:
            s = score_broll_for_caption(text, broll["id"], keyword_map)
            if s > best_score:
                best_score = s
                best_id = broll["id"]

        results.append({
            "caption_idx": i,
            "caption_text": text,
            "broll_id": best_id,
            "score": best_score,
            "fallback": best_score <= 0,
        })
    return results


def audit_caption_broll_mismatch(
    captions: list[dict],
    brolls: list[dict],
    keyword_map: Optional[dict[str, list[str]]] = None,
    min_score: float = 0.5,
) -> dict:
    """Audit captions that have weak or no b-roll match.

    Returns:
        {
            'total': int,
            'matched': int,
            'weak': int,
            'unmatched': int,
            'details': list[dict],
        }
    """
    matches = match_brolls_to_captions(captions, brolls, keyword_map)
    matched = sum(1 for m in matches if m["score"] >= min_score)
    weak = sum(1 for m in matches if 0 < m["score"] < min_score)
    unmatched = sum(1 for m in matches if m["score"] <= 0)

    return {
        "total": len(matches),
        "matched": matched,
        "weak": weak,
        "unmatched": unmatched,
        "details": matches,
    }


def print_mismatch_report(audit: dict) -> None:
    """Pretty-print caption-to-broll mismatch audit."""
    print("=" * 60)
    print("Caption → B-Roll Mismatch Audit")
    print("=" * 60)
    print(f"\nTotal:     {audit['total']}")
    print(f"Matched:   {audit['matched']}")
    print(f"Weak:      {audit['weak']}")
    print(f"Unmatched: {audit['unmatched']}")

    for d in audit.get("details", []):
        flag = "" if d["score"] >= 0.5 else (" [WEAK]" if d["score"] > 0 else " [UNMATCHED]")
        print(f"  [{d['caption_idx']:3}] score={d['score']:.1f}{flag}")
        print(f"        caption: {d['caption_text'][:50]}")
        print(f"        broll:   {d['broll_id']}")


# ─────────────────────────────────────────────────────────────────────────────
# Auto-sequencer
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BrollAssignment:
    caption_idx: int
    caption_text: str
    broll_id: str
    trim_start_us: int
    trim_duration_us: int
    score: float
    fallback: bool = False


def auto_sequence_brolls(
    captions: list[dict],
    brolls: list[dict],
    total_duration_us: int,
    keyword_map: Optional[dict[str, list[str]]] = None,
) -> list[BrollAssignment]:
    """Assign b-roll clips to caption time slots, filling all gaps.

    Each caption's duration defines the b-roll trim window. Clips are
    reused (different trim points) if there are more captions than clips.

    Args:
        captions: list of {text, start_us, duration_us}
        brolls: list of {id, source_duration_us}
        total_duration_us: full timeline length in microseconds
        keyword_map: optional override for scoring

    Returns:
        list of BrollAssignment (one per caption, filling timeline)
    """
    if not captions or not brolls:
        return []

    matches = match_brolls_to_captions(captions, brolls, keyword_map)

    # Build a usage counter to vary trim offsets on repeated clips
    usage_counter: dict[str, int] = {}
    assignments: list[BrollAssignment] = []

    for cap, match in zip(captions, matches):
        broll_id = match["broll_id"] or brolls[0]["id"]
        broll = next((b for b in brolls if b["id"] == broll_id), brolls[0])

        use_count = usage_counter.get(broll_id, 0)
        source_dur = broll.get("source_duration_us", total_duration_us)
        cap_dur = cap.get("duration_us", total_duration_us // len(captions))

        # Stagger trim start so repeated clips don't show identical footage
        offset_us = (use_count * cap_dur) % max(1, source_dur - cap_dur)
        usage_counter[broll_id] = use_count + 1

        assignments.append(BrollAssignment(
            caption_idx=match["caption_idx"],
            caption_text=match["caption_text"],
            broll_id=broll_id,
            trim_start_us=int(offset_us),
            trim_duration_us=cap_dur,
            score=match["score"],
            fallback=match["fallback"],
        ))

    return assignments


def print_sequence_plan(
    assignments: list[BrollAssignment],
    total_duration_us: int,
) -> None:
    """Pretty-print the auto-sequenced b-roll plan."""
    S = 1_000_000
    print("=" * 60)
    print("Auto-Sequence Plan")
    print("=" * 60)
    print(f"Total duration: {total_duration_us / S:.1f}s | {len(assignments)} segments\n")

    for a in assignments:
        flag = " [FALLBACK]" if a.fallback else ""
        start_s = 0
        for i in range(a.caption_idx):
            pass
        print(f"  [{a.caption_idx:3}] {a.broll_id}  (score={a.score:.1f}){flag}")
        print(f"        trim={a.trim_start_us/S:.1f}s + {a.trim_duration_us/S:.1f}s")
        print(f"        caption: \"{a.caption_text[:50]}\"")
