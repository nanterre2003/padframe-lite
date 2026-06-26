"""
capcut_helpers.broll_audit — B-roll ratio and narration sync auditing.

Ensures b-roll footage covers the narration track with correct ratios
and that no narration segment is left without matching footage.
"""
import json
from typing import Optional


def _get_track_by_type(draft: dict, track_type: str) -> Optional[dict]:
    """Return the first track of the given type, or None."""
    for tr in draft.get("tracks", []):
        if tr.get("type") == track_type:
            return tr
    return None


def audit_broll_ratio(
    draft: dict,
    target_ratio: float = 0.8,
) -> dict:
    """Check that b-roll footage covers at least `target_ratio` of the timeline.

    Args:
        draft: full draft dict
        target_ratio: minimum fraction of narration that must be covered by b-roll
                      (0.8 = 80% coverage)

    Returns:
        {
            'total_narration_sec': float,
            'broll_covered_sec': float,
            'coverage_ratio': float,
            'passes': bool,
            'uncovered_gaps': list[dict],
        }
    """
    text_track = _get_track_by_type(draft, "text")
    video_track = _get_track_by_type(draft, "video")

    if not text_track or not video_track:
        return {
            "total_narration_sec": 0.0,
            "broll_covered_sec": 0.0,
            "coverage_ratio": 0.0,
            "passes": False,
            "uncovered_gaps": [],
        }

    def _segs_to_intervals(segs: list) -> list[tuple[float, float]]:
        intervals = []
        for seg in segs:
            tr = seg.get("target_timerange", {})
            start = tr.get("start", 0) / 1e6
            dur = tr.get("duration", 0) / 1e6
            if dur > 0:
                intervals.append((start, start + dur))
        return sorted(intervals)

    narration_intervals = _segs_to_intervals(text_track.get("segments", []))
    broll_intervals = _segs_to_intervals(video_track.get("segments", []))

    def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
        return max(0.0, min(a_end, b_end) - max(a_start, b_start))

    total_narration = sum(e - s for s, e in narration_intervals)
    covered = 0.0
    uncovered_gaps = []

    for n_start, n_end in narration_intervals:
        seg_covered = sum(
            overlap(n_start, n_end, b_start, b_end)
            for b_start, b_end in broll_intervals
        )
        covered += seg_covered
        if seg_covered < (n_end - n_start) * 0.9:
            uncovered_gaps.append({
                "start_sec": round(n_start, 2),
                "end_sec": round(n_end, 2),
                "coverage_sec": round(seg_covered, 2),
            })

    ratio = covered / total_narration if total_narration > 0 else 0.0

    return {
        "total_narration_sec": round(total_narration, 2),
        "broll_covered_sec": round(covered, 2),
        "coverage_ratio": round(ratio, 3),
        "passes": ratio >= target_ratio,
        "uncovered_gaps": uncovered_gaps,
    }


def audit_narration_sync(draft: dict, max_gap_sec: float = 0.3) -> dict:
    """Check that narration captions are tightly synced (no large gaps between segments).

    Args:
        draft: full draft dict
        max_gap_sec: maximum allowed gap between caption segments in seconds

    Returns:
        {
            'total_captions': int,
            'total_duration_sec': float,
            'sync_gaps': list[dict],
            'passes': bool,
        }
    """
    text_track = _get_track_by_type(draft, "text")
    if not text_track:
        return {"total_captions": 0, "total_duration_sec": 0.0, "sync_gaps": [], "passes": True}

    segs = text_track.get("segments", [])
    total_captions = len(segs)
    sync_gaps = []
    prev_end = None
    total_dur = 0.0

    for i, seg in enumerate(segs):
        tr = seg.get("target_timerange", {})
        start = tr.get("start", 0) / 1e6
        dur = tr.get("duration", 0) / 1e6
        end = start + dur
        total_dur = max(total_dur, end)

        if prev_end is not None:
            gap = start - prev_end
            if gap > max_gap_sec:
                texts = draft.get("materials", {}).get("texts", [])
                mat_id = seg.get("material_id", "")
                text = ""
                for t in texts:
                    if t.get("id") == mat_id:
                        try:
                            co = json.loads(t.get("content", "{}"))
                            text = co.get("text", "")[:40]
                        except json.JSONDecodeError:
                            pass
                        break
                sync_gaps.append({
                    "segment_idx": i,
                    "gap_sec": round(gap, 2),
                    "at_sec": round(start, 2),
                    "caption_preview": text,
                })
        prev_end = end

    return {
        "total_captions": total_captions,
        "total_duration_sec": round(total_dur, 2),
        "sync_gaps": sync_gaps,
        "passes": len(sync_gaps) == 0,
    }


def print_broll_audit(broll_report: dict, sync_report: dict) -> None:
    """Print combined b-roll and sync audit results."""
    print("=" * 60)
    print("B-Roll Audit")
    print("=" * 60)

    ratio = broll_report.get("coverage_ratio", 0) * 100
    status = "PASS" if broll_report.get("passes") else "FAIL"
    print(f"\nCoverage: {ratio:.1f}%  [{status}]")
    print(f"  Narration: {broll_report.get('total_narration_sec', 0)}s")
    print(f"  B-roll covered: {broll_report.get('broll_covered_sec', 0)}s")

    gaps = broll_report.get("uncovered_gaps", [])
    if gaps:
        print(f"\n  {len(gaps)} uncovered section(s):")
        for g in gaps[:5]:
            print(f"    {g['start_sec']}s–{g['end_sec']}s (covered: {g['coverage_sec']}s)")

    print(f"\nSync Gaps: {len(sync_report.get('sync_gaps', []))} gap(s)  "
          f"[{'PASS' if sync_report.get('passes') else 'WARN'}]")
    for g in sync_report.get("sync_gaps", [])[:5]:
        print(f"  {g['gap_sec']}s gap before seg {g['segment_idx']} at {g['at_sec']}s")
        if g.get("caption_preview"):
            print(f"    caption: \"{g['caption_preview']}\"")
