"""
config.example.py — Copy this to config.py and set your own paths.

You can define paths here OR as environment variables. paths.py reads from either.
Auto-detects the current user by default — no hardcoded account names needed.
"""

# ─────────────────────────────────────────────────────────────────────────────
# Required: your video project workspace (where assets/ videos/ live)
# ─────────────────────────────────────────────────────────────────────────────
# VIDEO_KIT_PROJECT_ROOT = "D:/MyYouTubeProject"

# ─────────────────────────────────────────────────────────────────────────────
# Optional: CapCut user-data directory (auto-detected if unset)
# ─────────────────────────────────────────────────────────────────────────────
# CAPCUT_USER_DATA = r"C:\Users\YourName\AppData\Local\CapCut\User Data"

# ─────────────────────────────────────────────────────────────────────────────
# Optional: capcut-cli npm shim path (for JSON automation)
# ─────────────────────────────────────────────────────────────────────────────
# CAPCUT_CLI = r"C:\Users\YourName\AppData\Roaming\npm\capcut-cli.cmd"

# Asset layout (under PROJECT_ROOT):
#   assets/bgm/        — background music tracks
#   assets/fonts/      — custom fonts (e.g. NotoSerifCJK-Bold.ttc)
#   assets/templates/  — CapCut draft template backups
#   videos/            — raw footage and exported videos
