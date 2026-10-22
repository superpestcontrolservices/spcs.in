#!/usr/bin/env python3
"""Generate review inventory and strong-claim review CSVs without editing pages."""

from __future__ import annotations

import csv
import argparse
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTIMONIALS_CSV = ROOT / "testimonials_inventory.csv"
CLAIMS_CSV = ROOT / "claims_review.csv"
REVIEW_SCRIPT = ROOT / "js" / "location-reviews.js"
CLAIM_PATTERN = re.compile(
    r"\b(?:NIPHM|IPCA|certified|certification|licensed|license|approved|approval|"
    r"guaranteed|guarantee|100\s*(?:%|percent)|no harm|completely safe|best|No\.?\s*1|"
    r"\d{2,3}\s+years?|three\s+decades|decades|since\s+(?:19|20)\d{2})(?!\w)",
    re.I,
)


def clean(fragment: str) -> str:
    return re.sub(
        r"\s+", " ",
        html.unescape(re.sub(r"<[^>]+>", " ", fragment, flags=re.S)),
    ).strip()


def extract_testimonials(path: Path, label: str) -> list[dict[str, str]]:
    source = path.read_text(encoding="utf-8", errors="replace")
    rows = []
    for match in re.finditer(
        r"<article\b[^>]*class=[\"'][^\"']*\breview-card\b[^\"']*[\"'][^>]*>(.*?)</article\s*>",
        source,
        re.I | re.S,
    ):
        body = match.group(1)
        quote = re.search(r"<p\b[^>]*>(.*?)</p\s*>", body, re.I | re.S)
        name = re.search(r"<strong\b[^>]*>(.*?)</strong\s*>", body, re.I | re.S)
        if quote and name:
            rows.append({
                "page": label,
                "name": clean(name.group(1)),
                "text start": clean(quote.group(1))[:180],
                "line": str(source.count("\n", 0, match.start()) + 1),
            })
    return rows


def claim_suggestion(term: str) -> str:
    lowered = term.casefold()
    if lowered in {"niphm", "ipca", "certified", "certification", "licensed", "license"}:
        return "Use only the exact owner-approved, evidence-backed wording; otherwise remove the credential claim."
    if lowered in {"approved", "approval"}:
        return "Name the approving authority/product basis only if verified; otherwise describe the treatment without this claim."
    if re.search(r"\b(?:years?|decades|since\s+(?:19|20)\d{2})\b", lowered):
        return "Replace only with the exact owner-approved experience wording; otherwise remove this unverified time-in-business claim."
    if lowered in {"guaranteed", "guarantee", "100%", "100 percent", "no harm", "completely safe", "best", "no.1", "no 1"}:
        return "Do not imply certainty or superiority; propose a specific, supportable description and obtain owner approval."
    return "Review context and substantiate; do not change testimonial wording without approval."


def build_reports(*, testimonials: bool = True, claims: bool = True) -> None:
    if testimonials:
        testimonial_rows = []
        html_pages = sorted(ROOT.rglob("*.html"))
        shared_reviews = extract_testimonials(REVIEW_SCRIPT, "") if REVIEW_SCRIPT.exists() else []
        for path in html_pages:
            if ".venv" in path.parts:
                continue
            label = path.relative_to(ROOT).as_posix()
            source = path.read_text(encoding="utf-8", errors="replace")
            testimonial_rows.extend(extract_testimonials(path, label))
            if re.search(r'<script\b[^>]*\bsrc=["\']/js/location-reviews\.js(?:\?[^"\']*)?["\']', source, re.I):
                for review in shared_reviews:
                    testimonial_rows.append({**review, "page": label})
        with TESTIMONIALS_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["page", "name", "text start", "line"])
            writer.writeheader()
            writer.writerows(testimonial_rows)
        print(f"Testimonial inventory rows: {len(testimonial_rows)}")

    if claims:
        claim_rows = []
        sources = [
            path for path in ROOT.rglob("*.html") if ".venv" not in path.parts
        ]
        if REVIEW_SCRIPT.exists():
            sources.append(REVIEW_SCRIPT)
        for path in sorted(sources):
            rel = path.relative_to(ROOT).as_posix()
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(),
                start=1,
            ):
                visible = clean(line)
                for match in CLAIM_PATTERN.finditer(visible):
                    term = match.group(0)
                    claim_rows.append({
                        "page": rel,
                        "line": str(line_number),
                        "phrase": term,
                        "suggested fix": claim_suggestion(term),
                    })
        with CLAIMS_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=["page", "line", "phrase", "suggested fix"])
            writer.writeheader()
            writer.writerows(claim_rows)
        print(f"Claims requiring owner review: {len(claim_rows)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--claims-only", action="store_true")
    group.add_argument("--testimonials-only", action="store_true")
    args = parser.parse_args()
    build_reports(
        testimonials=not args.claims_only,
        claims=not args.testimonials_only,
    )
