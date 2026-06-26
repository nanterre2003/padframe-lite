"""
silent_vlog_maker.audit_report — Markdown/JSON report generation.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from .audit import ClipAudit
from .scene_audit import Scene


def generate_markdown_report(
    clips: list[ClipAudit],
    scenes: list[Scene],
    output_path: Optional[Path] = None,
    title: str = "Video Autopilot Kit — Audit Report",
) -> str:
    """Generate a Markdown audit report for clips and scenes.

    Args:
        clips: list of ClipAudit results
        scenes: list of Scene clusters
        output_path: optional path to write .md file
        title: report title

    Returns: Markdown string
    """
    lines = [
        f"# {title}",
        f"",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"",
        f"## Summary",
        f"",
        f"- **Total clips:** {len(clips)}",
        f"- **Total scenes:** {len(scenes)}",
        f"- **Total duration:** {sum(c.duration_sec for c in clips):.1f}s",
        f"- **Clips with warnings:** {sum(1 for c in clips if c.warnings)}",
        f"",
        f"## Clip Audit",
        f"",
        f"| File | Duration | Resolution | Codec | Portrait | HDR | GPS | Warnings |",
        f"|------|----------|------------|-------|----------|-----|-----|----------|",
    ]

    for clip in clips:
        warns = "; ".join(clip.warnings) if clip.warnings else "—"
        res = f"{clip.width}×{clip.height}" if clip.exists else "N/A"
        lines.append(
            f"| {clip.path.name} | {clip.duration_sec:.1f}s | {res} | "
            f"{clip.codec} | {'✓' if clip.is_portrait else '✗'} | "
            f"{'✓' if clip.is_hdr else '—'} | {'✓' if clip.has_gps else '—'} | {warns} |"
        )

    lines += [
        f"",
        f"## Scene Timeline",
        f"",
    ]

    for i, scene in enumerate(scenes):
        start = scene.start_time.strftime("%H:%M") if scene.start_time else "?"
        end = scene.end_time.strftime("%H:%M") if scene.end_time else "?"
        lines.append(f"### Scene {i + 1}: {start}–{end}")
        lines.append(f"")
        lines.append(f"- Duration: {scene.total_duration_sec:.1f}s")
        lines.append(f"- Clips: {len(scene.clips)}")
        if scene.location_label:
            lines.append(f"- Location: {scene.location_label}")
        lines.append(f"")
        for clip in scene.clips:
            lines.append(f"  - `{clip.path.name}` ({clip.duration_sec:.1f}s)")
        lines.append(f"")

    report = "\n".join(lines)

    if output_path:
        output_path.write_text(report, encoding="utf-8")

    return report


def generate_json_report(
    clips: list[ClipAudit],
    scenes: list[Scene],
    output_path: Optional[Path] = None,
) -> dict:
    """Generate a structured JSON audit report.

    Returns: dict with full audit data
    """
    def _clip_to_dict(c: ClipAudit) -> dict:
        return {
            "path": str(c.path),
            "exists": c.exists,
            "duration_sec": c.duration_sec,
            "width": c.width,
            "height": c.height,
            "fps": c.fps,
            "codec": c.codec,
            "has_audio": c.has_audio,
            "pix_fmt": c.pix_fmt,
            "rotation": c.rotation,
            "has_gps": c.has_gps,
            "creation_time": c.creation_time,
            "is_portrait": c.is_portrait,
            "is_hdr": c.is_hdr,
            "warnings": c.warnings,
        }

    def _scene_to_dict(s: Scene) -> dict:
        return {
            "n_clips": len(s.clips),
            "total_duration_sec": s.total_duration_sec,
            "start_time": s.start_time.isoformat() if s.start_time else None,
            "end_time": s.end_time.isoformat() if s.end_time else None,
            "location_label": s.location_label,
            "clips": [c.path.name for c in s.clips],
        }

    report = {
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_clips": len(clips),
            "total_scenes": len(scenes),
            "total_duration_sec": sum(c.duration_sec for c in clips),
            "clips_with_warnings": sum(1 for c in clips if c.warnings),
        },
        "clips": [_clip_to_dict(c) for c in clips],
        "scenes": [_scene_to_dict(s) for s in scenes],
    }

    if output_path:
        output_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return report
