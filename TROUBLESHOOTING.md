# Troubleshooting Guide

Common issues and their solutions for the video-autopilot-kit workflow.

---

## CapCut Issues

### "My changes disappear when I reopen the CapCut project"

**Cause:** M18 — draft JSON files out of sync. CapCut reads `draft_content.json`
but you may have only edited `draft_info.json`, or the Timeline subfolder copies
diverged.

**Fix:**
```python
from capcut_helpers import save_draft_with_sync, verify_sync

save_draft_with_sync("YourProjectName", draft)  # writes all 7 copies
result = verify_sync("YourProjectName")
print(result["all_synced"])  # must be True
```

---

### "CapCut overwrites my edits immediately after saving"

**Cause:** M20 — CapCut was running while you edited JSON. It auto-saved its
in-memory cached state, overwriting your file.

**Fix:** Always kill CapCut before editing:
```python
from capcut_helpers import safe_kill_then_verify
safe_kill_then_verify()  # kills + verifies dead (3 retries)
```

---

### "The exported video still has B-roll original audio despite 4-level mute"

**Cause:** M29 / M55 — CapCut's export engine bypasses the JSON mute flags
under certain conditions.

**Fix:** ALWAYS post-process with `force_mix_bgm()`:
```python
from capcut_helpers import force_mix_bgm
force_mix_bgm(capcut_export.mp4, output.mp4, bgm_path=Path("bgm.mp3"))
```

---

### "Video is letterboxed in a landscape frame when I export portrait footage"

**Cause:** M46 — Default CapCut canvas is 1920×1080 landscape.

**Fix:** Set canvas to portrait after loading the draft:
```python
from capcut_helpers import set_canvas_portrait
set_canvas_portrait(draft)  # → 1080×1920, ratio "9:16"
```

---

### "Text effects (花字) are invisible after applying via script"

**Cause:** M47 — Effect material added but `effect_id` not linked, or segment
`extra_material_refs` not updated.

**Fix:** Use `apply_effect_to_segment()` which handles all three steps:
```python
from capcut_helpers import apply_effect_to_segment
apply_effect_to_segment(draft, segment_idx=0, effect_id="YOUR_EFFECT_ID")
```

---

### "Subtitle styles are broken after running corrections (range mismatch)"

**Cause:** M69b — Text replacement changed string length without updating
`styles[].range[1]`.

**Fix:** `apply_subtitle_corrections()` already handles this via the
`@validate_invariants` decorator. If you're writing custom corrections,
use the decorator:
```python
from capcut_helpers.invariants import validate_invariants, TEXT_MATERIAL_INVARIANTS, TEXT_MATERIAL_AUTO_FIX

@validate_invariants(TEXT_MATERIAL_INVARIANTS, TEXT_MATERIAL_AUTO_FIX, on_violation="warn")
def my_mutation(co, ...):
    co["text"] = ...
    return co
```

---

## FFmpeg Issues

### "ffmpeg command fails with 'No such file or directory'"

**Cause:** ffmpeg not on PATH, or path contains spaces/special characters.

**Fix:**
- Windows: install ffmpeg and add to PATH, or set full path in command
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg` or `dnf install ffmpeg`

Verify: `ffmpeg -version` and `ffprobe -version` both work.

---

### "Video has no audio after force_mix_bgm"

**Cause:** BGM file path is wrong, or BGM file is corrupted.

**Fix:** Verify BGM file is valid:
```bash
ffprobe -v error -show_format bgm.mp3
```

---

### "Sync drift between video and audio in final export"

**Cause:** M83 — Using NVENC with B-frames can cause player time-counter issues.

**Fix:** Re-encode with player-safe profile:
```python
from capcut_helpers import reencode_player_safe
reencode_player_safe(input.mp4, output.mp4)  # libx264, no B-frames, CFR
```

---

### "BGM fades out before video ends"

**Cause:** M79 v1 — Old behavior faded to silence when BGM shorter than video.

**Fix:** Ensure `loop_fill=True` (default in v2):
```python
force_mix_bgm(input, output, bgm, loop_fill=True)  # loops + crossfades
```

---

## Example Script Issues

### "examples/01_vertical_short.py fails"

Check:
1. ffmpeg/ffprobe on PATH: `ffmpeg -version`
2. Python 3.9+: `python --version`
3. Run from repo root: `python examples/01_vertical_short.py`

### "examples/02_caption_broll_match.py fails"

Check:
1. Python 3.9+: `python --version`
2. Run from repo root: `python examples/02_caption_broll_match.py`
3. No other dependencies needed — pure Python only

---

## Still Stuck?

Check the knowledge base in `knowledge/production_guide.md` for the lesson (M-number)
referenced in the error or function docstring.
