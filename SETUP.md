# SETUP.md — Personalization Questionnaire

Rather than shipping someone else's private settings, this kit gives you a
structured skeleton you personalize through this questionnaire.

**Quickstart:** Copy the three mandatory templates and fill only the starred (★)
sections to launch immediately. Add optional data later.

**AI Interview Mode:** Ask your AI assistant to interview you based on this file
— it will ask questions one-by-one and auto-generate profile templates from your answers.

---

## ★ Section 1: Brand & Channel (Required)

Answer these to generate `templates/brand_profile.md`:

1. **Channel name:** What is your channel called?
2. **Outro style:** How do you typically end your videos?
   - [ ] Text card (store name + address)
   - [ ] Social handle callout
   - [ ] Subscribe reminder
   - [ ] No standard outro
3. **On-camera presence:** Do you appear on camera?
   - [ ] Yes — face appears regularly
   - [ ] Voiceover only
   - [ ] No voice/face — silent footage + text

---

## ★ Section 2: Content Type & Niche (Required)

1. **Content niche:** [e.g. food vlog / travel / tech tutorial / lifestyle]
2. **Primary platform:** [YouTube / TikTok / Instagram]
3. **Language:** [e.g. English / Traditional Chinese / Japanese]
4. **Secondary platforms:** (optional)

---

## ★ Section 3: Production Setup (Required)

1. **CapCut Desktop:** Do you have CapCut Desktop installed?
   - [ ] Yes, on Windows
   - [ ] Yes, on macOS (limited features)
   - [ ] No — FFmpeg-only pipeline only
2. **Project root path:** Where do you keep your video project files?
   Example: `D:\MyYouTubeProject` or `/Users/yourname/Videos/YTProject`
3. **BGM folder:** Where do you keep background music?
   Default: `{PROJECT_ROOT}/assets/bgm/`

---

## ⭕ Section 4: Voice Profile (Optional — improves caption quality)

If you have examples of your narration or captions:

1. **Paste 3–5 caption examples** from your existing videos
2. **Describe your tone in one sentence** (e.g. "casual friend sharing a discovery")
3. **Words/phrases you avoid** (e.g. no "guys", no exclamation marks)
4. **Sign-off style** (how you typically end videos)

Copy your answers into `templates/voice_profile.md`.

---

## ⭕ Section 5: Algorithm Metrics (Optional — improves strategy)

From your analytics dashboard:

1. Average hook retention (0–3s): [N%]
2. Average view completion: [N%]
3. Best performing content type: [describe]
4. Typical posting time that performs best: [day + time]

Copy into `knowledge/algorithm_insights.md`.

---

## ⭕ Section 6: Community Strategy (Optional)

1. Do you have a newsletter, Discord, or messaging group?
2. How do you typically notify your community of new uploads?
3. Who are your recurring viewers / super fans? (rough description, no names)

---

## After Setup

1. Copy `config.example.py` → `config.py` and set your paths
2. Run `python examples/02_caption_broll_match.py` to verify Python + matcher work
3. Run `python examples/01_vertical_short.py` to verify the full ffmpeg pipeline
4. If using CapCut automation: open a test project and verify `draft_content.json` is editable

---

## Design Philosophy

> "The system's real value is structure and methodology, not someone else's private numbers."

All templates ship blank. You provide your voice, brand guidelines, and community data
— the kit provides the workflow that scales that content consistently.
