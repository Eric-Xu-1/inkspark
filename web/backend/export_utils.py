"""Markdown export formatting utilities."""

import re
from datetime import datetime
from typing import Dict
from urllib.parse import quote

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_EXCESS_NEWLINES = re.compile(r"\n{3,}")


def sanitize_filename(name: str, max_len: int = 80) -> str:
    cleaned = _INVALID_FILENAME_CHARS.sub("", name).strip().rstrip(".")
    if not cleaned:
        return "article"
    return cleaned[:max_len]


def build_content_disposition(filename: str) -> str:
    base = sanitize_filename(filename)
    utf8_name = base if base.endswith(".md") else f"{base}.md"
    ascii_name = base.encode("ascii", "ignore").decode().strip() or "article"
    if not ascii_name.endswith(".md"):
        ascii_name = f"{ascii_name}.md"
    encoded = quote(utf8_name)
    return f'attachment; filename="{ascii_name}"; filename*=UTF-8\'\'{encoded}'


def _escape_yaml(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _build_front_matter(data: Dict[str, str]) -> str:
    title = data.get("article_title") or data.get("topic") or "文章"
    lines = ["---", f'title: "{_escape_yaml(title)}"']

    topic = data.get("topic", "")
    if topic and topic != title:
        lines.append(f'topic: "{_escape_yaml(topic)}"')

    for key, label in (("mode", "mode"), ("category", "category")):
        value = data.get(label, "")
        if value:
            lines.append(f'{key}: "{_escape_yaml(value)}"')

    created = data.get("created_at", "")
    if created:
        try:
            dt = datetime.fromtimestamp(float(created))
            lines.append(f'date: "{dt.strftime("%Y-%m-%d")}"')
        except (ValueError, TypeError, OSError):
            pass

    lines.append("---")
    return "\n".join(lines)


def _clean_markdown(text: str) -> str:
    return _EXCESS_NEWLINES.sub("\n\n", text.strip())


def format_export_markdown(data: Dict[str, str]) -> str:
    body = data.get("export") or data.get("full_article", "")
    if not body:
        return ""

    body = _clean_markdown(body)
    front_matter = _build_front_matter(data)
    return f"{front_matter}\n\n{body}\n"
