# Production Methodology Guide (M1–M50)

This knowledge base documents production lessons learned, anti-patterns, and
validated approaches for the video-autopilot-kit workflow.

---

## M18 — Draft JSON Synchronization (Critical)

**Problem:** CapCut writes to `draft_info.json` but reads from `draft_content.json`.
When files diverge, CapCut silently overwrites newer changes with stale state on load.

**Solution:** Always use `save_draft_with_sync()` which writes to all 7 locations:
- `draft_content.json` (root)
- `draft_info.json` (root)
- `Timelines/<UUID>/draft_content.json`
- `Timelines/<UUID>/draft_info.json`
- Backup copies with timestamps

**Verification:** Run `verify_sync(project_name)` after every save.

---

## M20 — Kill CapCut Before Editing JSON

**Problem:** If CapCut is running while you edit JSON externally, it auto-saves
its cached in-memory state on next interaction, overwriting your edits.

**Solution:** Always call `safe_kill_then_verify()` before editing draft JSON.
Verify with `is_capcut_running()` before proceeding.

---

## M29 — 4-Level Mute (Critical)

**Problem:** Setting `segment.volume = 0` alone still leaks B-roll original audio in exports.

**Solution:** All four levels must be set simultaneously:
1. `material.has_audio = false`
2. `material.has_sound_separated = true`
3. `segment.volume = 0`
4. `segment.last_nonzero_volume = 0`

**Code:** `mute_all_video_segments(draft)` handles all four levels.

**Fallback:** If still leaking, use `force_mix_bgm()` to replace audio track entirely.

---

## M46 — Canvas Orientation Fix

**Problem:** `capcut-cli init` defaults to 1920×1080 landscape canvas.
Portrait source footage (rotation=-90) exports letterboxed inside landscape frame.

**Solution:** Explicitly set canvas to portrait after init:
```python
set_canvas_portrait(draft)  # → 1080×1920, ratio "9:16"
```

---

## M47 — Effect Application

**Problem:** Adding effect materials without properly linking `effect_id` field,
or without adding entry id to `segment.extra_material_refs`, causes effects
to be invisible when CapCut opens the project.

**Solution:** Use `apply_effect_to_segment()` which:
1. Verifies effect cache path exists
2. Creates full materials.effects schema entry
3. Adds id to segment.extra_material_refs

---

## M55 — FFmpeg Post-Export Audio (Critical)

**Problem:** CapCut export, even with 100% JSON 4-level mute, still leaks B-roll audio.

**Solution:** ALWAYS run `force_mix_bgm()` after CapCut export.
This replaces the entire audio track with BGM-only.

**Warning (M84):** `force_mix_bgm()` strips voiceover entirely.
For teaching/narrated videos, use single-pass ffmpeg with `-t` trim instead.

---

## M56 — Outro Card Standard

Food vlog outro format: store name + address + optional phone/hours.

```python
add_outro_card(
    input_mp4, output_mp4,
    title_line="Store Name Branch",
    address_line="City Street 123",
    extra_line="(02) 1234-5678",  # optional
)
```

---

## M69 — Subtitle Correction (M69b fix)

**Problem:** CapCut AI transcription generates phonetic homophones and brand name errors.
Naive text replacement without syncing `styles[].range[1]` corrupts the style schema
(styles array range must always match text length).

**Solution:** Use `apply_subtitle_corrections()` which wraps mutations with
`@validate_invariants` decorator that auto-fixes `styles_range_match_text_len`.

---

## M73 — Styles Range Invariant

**Invariant:** For every style entry in a text material's content JSON,
`styles[n].range[1]` must equal `len(text)`.

**Auto-fix:** `_fix_styles_range()` is registered in `TEXT_MATERIAL_AUTO_FIX`
and runs automatically via `@validate_invariants` decorator.

---

## M79 — BGM Loop Fill (v2, 2026-06-01)

**Problem (v1):** BGM shorter than video duration faded to silence mid-video.

**Solution (v2):** `force_mix_bgm(loop_fill=True)` (default) uses `acrossfade`
to loop BGM seamlessly. Crossfade at song-end × song-start (1.5s by default).

---

## M82 — Voice End Detection

**Pattern:** Many CapCut timelines extend beyond the voiceover with silent B-roll.
Exporting at full timeline length wastes 30–60s of dead air.

**Solution:** `detect_voice_end()` uses `ffmpeg silencedetect` to find the last
silence start that extends to EOF, returning the true voice endpoint.

Then: `trim_to_voice_end()` → trims + re-encodes in one step.

---

## M83 — Player-Safe Re-encode

**Problem:** NVENC output with B-frames causes time-counter drift in some players
(PotPlayer, local preview tools). ffprobe PTS is correct; only UI display is off.

**Solution:** `reencode_player_safe()` uses libx264 with `-bf 0` (no B-frames),
CFR, closed GOP, no faststart. This is the "FINAL ship" profile.

---

## M91–M95 — Delivery QA Checklist

Run `run_full_qa(media_path)` before delivery:

- **M91** Dead air detection (>3s silence)
- **M92** Flash risk (rapid cuts >3Hz)
- **M93** Image layout verification (dimensions match target)
- **M94** Browser compatibility (H.264, yuv420p, AAC, faststart)
- **M95** Still image / jumpy cut detection (<0.5s scenes)

---

## Production Workflow (Standard)

```
1. kill CapCut (M20)
2. load_draft() 
3. set_canvas_portrait() (M46)
4. mute_all_video_segments() (M29)
5. apply_subtitle_corrections()
6. apply_text_preset_to_all() or apply_teaching_dual_tier()
7. audit_draft() — verify state
8. save_draft_with_sync() (M18)
9. Open CapCut → verify → Export
10. force_mix_bgm() (M55)
11. trim_to_voice_end() (M82)
12. reencode_player_safe() (M83)
13. run_full_qa() (M91–M95)
14. add_outro_card() if needed (M56)
```
