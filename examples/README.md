# Examples

Self-contained, runnable demonstrations that generate test materials without requiring CapCut or real footage.

## 01 — Vertical Short (end-to-end)

```bash
python examples/01_vertical_short.py
```

**Requires:** Python 3.9+ and `ffmpeg`/`ffprobe` on PATH.

Synthesizes two test landscape clips and a music track entirely with ffmpeg, then runs the full `silent_vlog_maker` pipeline (normalize → multi-color captions → BGM highlight) to produce a finished 1080×1920 MP4. No real media needed.

## 02 — Caption ↔ B-Roll Auto-Matching

```bash
python examples/02_caption_broll_match.py
```

**Requires:** Python 3.9+ only. No ffmpeg, no CapCut.

Demonstrates zero-config b-roll matching: captions are automatically aligned to footage by shared words in the filename. Name your clips after their content (`coffee.mp4`, `sunset.mov`, `ramen.mp4`) and the matcher does the rest — no keyword map needed.
