"""
capcut_helpers.mute — 4-level mute for CapCut exports.

M29 lesson: segment volume=0 alone leaks B-roll original audio.
Must mute at all four levels simultaneously to silence cleanly.

If the 4-level approach still leaks, use ffmpeg post_export.force_mix_bgm()
to force-replace the audio track as a final fallback.
"""


def _find_material(draft: dict, material_id: str) -> dict | None:
    """Find a video material entry by id."""
    for mat in draft.get("materials", {}).get("videos", []):
        if mat.get("id") == material_id:
            return mat
    return None


def _apply_4level_mute(seg: dict, material: dict | None) -> list[str]:
    """Apply all 4 mute levels to a segment + its material. Returns list of levels applied."""
    applied = []

    # Level 1 + 2: material flags
    if material is not None:
        material["has_audio"] = False
        applied.append("material.has_audio=false")
        material["has_sound_separated"] = True
        applied.append("material.has_sound_separated=true")

    # Level 3 + 4: segment volume
    seg["volume"] = 0
    applied.append("segment.volume=0")
    seg["last_nonzero_volume"] = 0
    applied.append("segment.last_nonzero_volume=0")

    return applied


def mute_all_video_segments(draft: dict) -> tuple[int, int]:
    """Apply 4-level mute to every video segment and its associated material.

    Returns:
        (segments_muted, materials_muted)
    """
    segs_muted = 0
    mats_muted = 0
    muted_mat_ids: set[str] = set()

    for track in draft.get("tracks", []):
        if track.get("type") != "video":
            continue
        for seg in track.get("segments", []):
            mat_id = seg.get("material_id", "")
            mat = _find_material(draft, mat_id)
            if mat and mat_id not in muted_mat_ids:
                muted_mat_ids.add(mat_id)
                mats_muted += 1
            _apply_4level_mute(seg, mat)
            segs_muted += 1

    return segs_muted, mats_muted


def mute_specific_segments(draft: dict, segment_indices: list[int]) -> tuple[int, int]:
    """Apply 4-level mute to selected video segments by 0-based index.

    Args:
        draft: full draft JSON dict
        segment_indices: list of 0-based indices into the first video track's segments

    Returns:
        (segments_muted, materials_muted)
    """
    video_tracks = [tr for tr in draft.get("tracks", []) if tr.get("type") == "video"]
    if not video_tracks:
        return 0, 0

    segments = video_tracks[0].get("segments", [])
    segs_muted = 0
    mats_muted = 0
    muted_mat_ids: set[str] = set()

    for idx in segment_indices:
        if idx < 0 or idx >= len(segments):
            continue
        seg = segments[idx]
        mat_id = seg.get("material_id", "")
        mat = _find_material(draft, mat_id)
        if mat and mat_id not in muted_mat_ids:
            muted_mat_ids.add(mat_id)
            mats_muted += 1
        _apply_4level_mute(seg, mat)
        segs_muted += 1

    return segs_muted, mats_muted


def audit_mute_state(draft: dict) -> dict:
    """Validate that all video segments meet the full 4-level mute criteria.

    Returns:
        {
            'total_segments': int,
            'fully_muted': int,
            'partial_muted': list[tuple[int, list[str]]],  # (idx, missing_levels)
            'success_rate': float,
        }
    """
    total = 0
    fully_muted = 0
    partial_muted: list[tuple[int, list[str]]] = []

    for track in draft.get("tracks", []):
        if track.get("type") != "video":
            continue
        for idx, seg in enumerate(track.get("segments", [])):
            total += 1
            mat_id = seg.get("material_id", "")
            mat = _find_material(draft, mat_id)

            missing = []
            if mat is not None:
                if mat.get("has_audio", True) is not False:
                    missing.append("material.has_audio")
                if not mat.get("has_sound_separated", False):
                    missing.append("material.has_sound_separated")
            if seg.get("volume", 1) != 0:
                missing.append("segment.volume")
            if seg.get("last_nonzero_volume", 1) != 0:
                missing.append("segment.last_nonzero_volume")

            if not missing:
                fully_muted += 1
            else:
                partial_muted.append((idx, missing))

    return {
        "total_segments": total,
        "fully_muted": fully_muted,
        "partial_muted": partial_muted,
        "success_rate": fully_muted / total if total else 0.0,
    }
