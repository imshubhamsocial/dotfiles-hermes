"""
Google Antigravity 2.0 (AGY) Artifacts Engine for Hermes Agent OS.
Complies strictly with AGY Generative UI, Artifact and Surface presentation specs:
1. Isolated storage at <appDataDir>/brain/<conversation-id>/
2. GitHub-style alerts (> [!NOTE], [!TIP], [!IMPORTANT], [!WARNING], [!CAUTION])
3. Mermaid inline diagrams with quote sanitation
4. Four-backtick multi-slide carousels
5. Standalone Generative UI HTML auxiliary pane apps (KaTeX, Chart.js, Canvas)
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_default_brain_dir(conversation_id: Optional[str] = None) -> Path:
    """Resolves the canonical AGY brain storage directory."""
    conv_id = conversation_id or os.environ.get("CONVERSATION_ID", "default_hermes_session")
    app_data_dir = os.environ.get("ANTIGRAVITY_APP_DATA_DIR")
    if app_data_dir:
        base = Path(app_data_dir) / "brain" / conv_id
    else:
        # Fallback to user home .gemini or .hermes
        gemini_brain = Path.home() / ".gemini" / "antigravity-cli" / "brain" / conv_id
        if gemini_brain.parent.exists():
            base = gemini_brain
        else:
            base = Path.home() / ".hermes" / "brain" / conv_id
    base.mkdir(parents=True, exist_ok=True)
    (base / "scratch").mkdir(parents=True, exist_ok=True)
    return base


class AGYArtifactsManager:
    """Manages creation, formatting, and validation of AGY artifacts."""

    VALID_ALERT_LEVELS = {"NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"}
    VALID_MERMAID_TYPES = {
        "flowchart TD", "flowchart LR", "graph TD", "graph LR",
        "sequenceDiagram", "stateDiagram-v2", "stateDiagram",
        "classDiagram", "erDiagram", "xychart-beta"
    }

    def __init__(self, conversation_id: Optional[str] = None, brain_dir: Optional[Path] = None):
        self.conversation_id = conversation_id or os.environ.get("CONVERSATION_ID", "default_hermes_session")
        self.brain_dir = brain_dir or get_default_brain_dir(self.conversation_id)
        self.scratch_dir = self.brain_dir / "scratch"
        self.manifest_path = self.brain_dir / "artifacts_manifest.jsonl"

    @classmethod
    def format_alert(cls, level: str, text: str) -> str:
        """Formats GitHub-style alert block with AGY compliance."""
        lvl = level.upper()
        if lvl not in cls.VALID_ALERT_LEVELS:
            lvl = "NOTE"
        lines = text.strip().splitlines()
        formatted_lines = [f"> [!{lvl}]"] + [f"> {line}" for line in lines]
        return "\n".join(formatted_lines)

    @classmethod
    def format_mermaid(cls, diagram_type: str, body: str) -> str:
        """Formats and sanitizes inline Mermaid diagram block."""
        dtype = diagram_type.strip()
        # Ensure diagram type is supported
        matched = False
        for valid in cls.VALID_MERMAID_TYPES:
            if dtype.startswith(valid):
                matched = True
                break
        if not matched:
            dtype = "flowchart TD"

        # Sanitize body node labels: quote labels with parentheses or brackets
        lines = []
        for line in body.strip().splitlines():
            # If line contains node definitions like id[Label (Extra)] without inner quotes, sanitize
            sanitized = re.sub(r'\[([^"\'\]]*\([^)]*\)[^"\'\]]*)\]', r'["\1"]', line)
            lines.append(sanitized)

        diagram_content = "\n".join(lines)
        return f"```mermaid\n{dtype}\n{diagram_content}\n```"

    @classmethod
    def format_carousel(cls, slides: List[str]) -> str:
        """Formats 4-backtick carousel with multiple slides."""
        if not slides:
            return ""
        slides_text = "\n<!-- slide -->\n".join(s.strip() for s in slides)
        return f"````carousel\n{slides_text}\n````"

    def create_markdown_artifact(
        self,
        filename: str,
        title: str,
        content: str,
        summary: str,
        user_facing: bool = True,
        request_feedback: bool = False,
    ) -> Path:
        """Creates a persistent markdown artifact in the AGY brain directory."""
        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        target_file = self.brain_dir / filename
        meta = {
            "title": title,
            "filename": filename,
            "summary": summary,
            "user_facing": user_facing,
            "request_feedback": request_feedback,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "conversation_id": self.conversation_id,
        }

        # Write markdown content
        target_file.write_text(content, encoding="utf-8")

        # Record in manifest
        with open(self.manifest_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(meta) + "\n")

        return target_file

    def create_html_auxiliary_app(
        self,
        filename: str,
        title: str,
        html_body: str,
        js_scripts: Optional[str] = None,
        css_styles: Optional[str] = None,
        include_katex: bool = True,
        include_charts: bool = True,
    ) -> Path:
        """Generates a standalone single-file HTML Generative UI application."""
        if not filename.endswith(".html"):
            filename = f"{filename}.html"

        target_file = self.brain_dir / filename

        cdn_head = []
        if include_katex:
            cdn_head.append('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">')
            cdn_head.append('<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>')
        if include_charts:
            cdn_head.append('<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>')

        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {' '.join(cdn_head)}
    <style>
        :root {{
            --bg: #0f172a;
            --card: #1e293b;
            --text: #f8fafc;
            --accent: #38bdf8;
            --border: #334155;
        }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 1.5rem;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: var(--card);
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid var(--border);
        }}
        {css_styles or ''}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {html_body}
    </div>
    <script>
        {js_scripts or ''}
    </script>
</body>
</html>"""
        target_file.write_text(html_template, encoding="utf-8")
        return target_file

    def list_artifacts(self) -> List[Dict[str, Any]]:
        """Lists all registered artifacts for the current session."""
        if not self.manifest_path.exists():
            return []
        items = []
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        items.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
        return items
