from __future__ import annotations

import re
from typing import Optional


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s\-\(\)]{6,}\d")


def scrub_text(payload: Optional[str]) -> str:
    """
    Best-effort redaction for text that might contain emails or phone numbers.
    """
    if not payload:
        return ""
    sanitized = EMAIL_RE.sub("[EMAIL]", payload)
    sanitized = PHONE_RE.sub("[PHONE]", sanitized)
    return sanitized.strip()


def summarize_for_log(payload: Optional[str], limit: int = 160) -> str:
    text = scrub_text(payload)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."

