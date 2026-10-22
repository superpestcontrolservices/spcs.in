#!/usr/bin/env python3
"""Create a blank local-notes worksheet from the launch report's flagged pairs."""

from __future__ import annotations

import csv
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "LAUNCH_READINESS_REPORT.md"
TEMPLATE = ROOT / "local_notes_template.csv"
FLAGGED_PATHS = ROOT / "data" / "overlap-flagged-pages.json"
FIELDS = [
    "district",
    "area",
    "landmarks_or_known_places",
    "typical_property_types",
    "pests_commonly_seen",
    "seasonal_notes",
    "real_job_example",
    "photo_available",
]


class HeadingParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.capture = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        if tag == "h1":
            self.capture = True

    def handle_endtag(self, tag):
        if tag == "h1":
            self.capture = False

    def handle_data(self, data):
        if self.capture:
            self.text.append(data)


def page_headings(path: Path) -> str:
    parser = HeadingParser()
    parser.feed(path.read_text(encoding="utf-8", errors="replace"))
    return re.sub(r"\s+", " ", " ".join(parser.text)).strip()


def flagged_paths() -> list[str]:
    report = REPORT.read_text(encoding="utf-8")
    found = set()
    for line in report.splitlines():
        if not re.match(r"^\|\s*\d{2}\.\d%\s*\|", line):
            continue
        for value in re.findall(r"`([^`]+\.html)`", line):
            if (ROOT / value.replace("/", "\\")).is_file():
                found.add(value.replace("\\", "/"))
    found.update(
        f"pest-control-in-{district}/index.html"
        for district in ("nagaur", "pali", "tonk", "udaipur")
    )
    return sorted(found)


def create() -> None:
    paths = flagged_paths()
    rows = []
    for relative in paths:
        path = ROOT / relative.replace("/", "\\")
        heading = page_headings(path) if path.exists() else ""
        match = re.match(r"pest-control-in-([^/]+)/([^/]+)/index\.html$", relative)
        if match:
            district = match.group(1).replace("_", " ").replace("-", " ").title()
            area = match.group(2).replace("_", " ").replace("-", " ").title()
            if "," in heading:
                heading_parts = heading.split(",", 1)
                area = heading_parts[0].replace("Pest Control in ", "").strip()
                district = heading_parts[1].strip()
        else:
            district = relative.split("/", 1)[0].removeprefix("pest-control-in-").replace("_", " ").replace("-", " ").title()
            area = ""
        rows.append({
            "district": district,
            "area": area,
            "landmarks_or_known_places": "",
            "typical_property_types": "",
            "pests_commonly_seen": "",
            "seasonal_notes": "",
            "real_job_example": "",
            "photo_available": "",
        })
    with TEMPLATE.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    FLAGGED_PATHS.parent.mkdir(parents=True, exist_ok=True)
    FLAGGED_PATHS.write_text(
        __import__("json").dumps(paths, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Flagged page rows: {len(rows)}")
    print(f"Notes template: {TEMPLATE.name}")
    print(f"Overlap page index: {FLAGGED_PATHS.relative_to(ROOT)}")


if __name__ == "__main__":
    create()
