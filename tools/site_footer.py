"""Shared site footer used by generated pages."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
from tools.site_claims import approved_claim


@lru_cache(maxsize=1)
def main_footer_html() -> str:
    homepage = (ROOT / "index.html").read_text(encoding="utf-8")
    match = re.search(r"<footer\b.*?</footer>", homepage, re.I | re.S)
    if match is None:
        raise ValueError("Could not find the main footer in the homepage")
    footer = match.group()
    approved_experience = approved_claim("experienceWording")
    footer_claim = (
        approved_experience
        if approved_experience
        else "Pest management services for homes, businesses and institutions."
    )
    footer = re.sub(
        r"<p\b([^>]*)>.*?(?:\b(?:28|30)\s+years?\b|three\s+decades|since\s+(?:19|20)\d{2}).*?</p\s*>",
        lambda item: f"<p{item.group(1)}>{footer_claim}</p>",
        footer,
        count=1,
        flags=re.I | re.S,
    )
    return footer


def apply_main_footer(page: str) -> str:
    matches = list(re.finditer(r"<footer\b.*?</footer>", page, re.I | re.S))
    if len(matches) != 1:
        raise ValueError(f"Expected one footer in generated page, found {len(matches)}")
    match = matches[0]
    footer = main_footer_html()
    return page[: match.start()] + footer + page[match.end() :]
