#!/usr/bin/env python3
"""Re-run the five-word shingle screen for nested location pages."""

from __future__ import annotations

import csv
import html
import re
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAIRS_CSV = ROOT / "overlap_pairs.csv"
CANDIDATES_CSV = ROOT / "overlap_candidates.csv"
NOTES_CSV = ROOT / "local_notes_template.csv"
WORDS = re.compile(r"\w+", re.UNICODE)
TOKEN_TAGS = {"script", "style", "noscript"}
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}
SHINGLE_SIZE = 5
THRESHOLD = 0.50


class MainTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_main = False
        self.skip_depth = 0
        self.depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if tag == "main" and not self.in_main:
            self.in_main = True
            return
        if not self.in_main:
            return
        self.depth += 1
        if self.skip_depth:
            if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
                self.skip_depth += 1
            return
        style = (attributes.get("style") or "").casefold().replace(" ", "")
        hidden = (
            tag in TOKEN_TAGS
            or "hidden" in attributes
            or (attributes.get("aria-hidden") or "").casefold() == "true"
            or "display:none" in style
            or "visibility:hidden" in style
        )
        if hidden:
            if tag not in VOID_TAGS:
                self.skip_depth = 1

    def handle_endtag(self, tag: str) -> None:
        if not self.in_main:
            return
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag == "main" and self.depth == 0:
            self.in_main = False
            return
        self.depth = max(0, self.depth - 1)
        if tag == "main":
            self.in_main = False

    def handle_data(self, data: str) -> None:
        if self.in_main and not self.skip_depth:
            self.parts.append(data)


def page_tokens(path: Path) -> list[str]:
    parser = MainTextParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    text = html.unescape(" ".join(parser.parts)).casefold()
    return WORDS.findall(text)


def shingles(tokens: list[str]) -> set[tuple[str, ...]]:
    return {
        tuple(tokens[index:index + SHINGLE_SIZE])
        for index in range(len(tokens) - SHINGLE_SIZE + 1)
    }


def load_local_notes() -> dict[tuple[str, str], bool]:
    notes: dict[tuple[str, str], bool] = {}
    if not NOTES_CSV.exists():
        return notes
    with NOTES_CSV.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            key = (
                row.get("district", "").strip().casefold(),
                row.get("area", "").strip().casefold(),
            )
            notes[key] = any(
                row.get(field, "").strip()
                for field in (
                    "landmarks_or_known_places",
                    "typical_property_types",
                    "pests_commonly_seen",
                    "seasonal_notes",
                    "real_job_example",
                )
            )
    return notes


def normalized_location_name(value: str) -> str:
    return value.replace("_", " ").replace("-", " ").casefold().strip()


def page_has_local_notes(page: str, notes: dict[tuple[str, str], bool]) -> bool:
    parts = Path(page).parts
    key = (
        normalized_location_name(parts[0].removeprefix("pest-control-in-")),
        normalized_location_name(parts[1]),
    )
    return notes.get(key, False)


def main() -> None:
    district_pages = list(ROOT.glob("pest-control-in-*/index.html"))
    area_pages = [
        path for path in ROOT.glob("pest-control-in-*/*/index.html")
        if "<!-- GENERATED AREA PAGE:" in path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    ]
    pages = sorted(set(district_pages + area_pages))
    page_data = []
    for path in pages:
        if path.parent.name.startswith("pest-control-in-"):
            district = path.parent.name.removeprefix("pest-control-in-")
            area = ""
            page_type = "district"
        else:
            district = path.parent.parent.name.removeprefix("pest-control-in-")
            area = path.parent.name
            page_type = "area"
        page_data.append((path, district, area, page_type, shingles(page_tokens(path))))

    similarities = []
    highest_by_page: dict[str, tuple[float, str]] = {}
    page_types = {}
    for path, _, _, page_type, _ in page_data:
        page_types[path.relative_to(ROOT).as_posix()] = page_type
    for index, (path_a, _, _, _, shingles_a) in enumerate(page_data):
        if not shingles_a:
            continue
        for path_b, _, _, _, shingles_b in page_data[index + 1:]:
            if not shingles_b:
                continue
            score = len(shingles_a & shingles_b) / min(len(shingles_a), len(shingles_b))
            if score < THRESHOLD:
                continue
            rel_a = path_a.relative_to(ROOT).as_posix()
            rel_b = path_b.relative_to(ROOT).as_posix()
            similarities.append((rel_a, rel_b, score))
            for page, pair in ((rel_a, rel_b), (rel_b, rel_a)):
                if score > highest_by_page.get(page, (0.0, ""))[0]:
                    highest_by_page[page] = (score, pair)

    similarities.sort(key=lambda item: (-item[2], item[0], item[1]))
    with PAIRS_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["page_a", "page_b", "containment_percent"])
        writer.writerows((a, b, f"{score:.1%}") for a, b, score in similarities)

    notes = load_local_notes()
    with CANDIDATES_CSV.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["page", "highest_pair_percent", "paired_page", "decision"])
        for page, (score, paired_page) in sorted(
            highest_by_page.items(), key=lambda item: (-item[1][0], item[0])
        ):
            if page_types.get(page) != "area":
                continue
            if page_has_local_notes(page, notes):
                continue
            writer.writerow(
                (
                    page,
                    f"{score:.1%}",
                    paired_page,
                    "Owner decision: improve with verified notes, merge, or noindex",
                )
            )

    print(f"Location pages screened: {len(page_data)}")
    print(f"District pages: {len(district_pages)}; area pages: {len(area_pages)}")
    print(f"Pairs at or above 50%: {len(similarities)}")
    print(f"Pairs at or above 60%: {sum(score >= 0.60 for _, _, score in similarities)}")
    area_candidates = (
        page for page in highest_by_page
        if page_types.get(page) == "area" and not page_has_local_notes(page, notes)
    )
    print(
        "Area pages with a >=50% pair and no local notes: "
        f"{sum(1 for _ in area_candidates)}"
    )
    print(f"Pair report: {PAIRS_CSV.name}")
    print(f"Owner-decision candidates: {CANDIDATES_CSV.name}")


if __name__ == "__main__":
    main()
