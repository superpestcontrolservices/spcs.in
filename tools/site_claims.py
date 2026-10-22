"""Read owner-approved public claims from the single site claims data file."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_FILE = ROOT / "data" / "site-claims.json"


def load_site_claims() -> dict:
    return json.loads(CLAIMS_FILE.read_text(encoding="utf-8"))


def approved_claim(name: str) -> str | None:
    value = load_site_claims().get(name)
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value.startswith("[[TO-FILL"):
        return None
    return value
