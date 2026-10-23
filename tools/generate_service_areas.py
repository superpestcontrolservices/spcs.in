#!/usr/bin/env python3
"""Generate reviewed Rajasthan service-area pages from the supplied workbook."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import posixpath
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
import zlib
import hashlib
from collections import defaultdict
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_footer import apply_main_footer
from tools.page_images import image_for_district
from tools.site_claims import approved_claim, load_site_claims
from tools.site_schema import website_schema


COPY_FILE = ROOT / "data" / "service-area-copy.json"
SITEMAP_FILE = ROOT / "sitemap.xml"
BASE_URL = "https://www.superpest.in"
SHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
AREA_MARKER_START = "<!-- BEGIN GENERATED AREAS WE SERVE -->"
AREA_MARKER_END = "<!-- END GENERATED AREAS WE SERVE -->"
AREA_LINKS_START = "<!-- BEGIN GENERATED AREA LINKS -->"
AREA_LINKS_END = "<!-- END GENERATED AREA LINKS -->"
LEGACY_NOTE_START = "<!-- BEGIN LEGACY AREA NOTE -->"
LEGACY_NOTE_END = "<!-- END LEGACY AREA NOTE -->"
PAGE_MARKER = "<!-- GENERATED AREA PAGE:"

SERVICES = [
    ("Termite Control", "/services/termite-control/"),
    ("General Pest Control", "/services/general-pest-control/"),
    ("Wasp & Hornet Nest Removal", "/services/wasp-hornet-nest-removal/"),
    ("Rodent Management", "/services/rodent-management/"),
    ("Vector Control & Fogging", "/services/vector-control-fogging/"),
    ("Bed Bug Eradication", "/services/bed-bug-eradication/"),
    ("Wood Borer Control", "/services/wood-borer-control/"),
    ("Commercial Fumigation", "/services/commercial-fumigation/"),
    ("Fly Management Systems", "/services/fly-management-systems/"),
    ("Sanitization & Disinfection", "/services/sanitization-disinfection/"),
    ("Commercial AMC (IPM)", "/services/commercial-amc-ipm/"),
]
PARENT_ALIASES = {"salumber": "salumbar"}
AREA_STYLE = """
<style>
    .area-breadcrumb { width: min(1200px, 90%); margin: 24px auto 0; color: #59665f; font-size: 14px; }
    .area-breadcrumb ol { display: flex; flex-wrap: wrap; gap: 8px; list-style: none; }
    .area-breadcrumb li + li::before { content: "/"; margin-right: 8px; color: #87918a; }
    .area-breadcrumb a, .area-content a { color: #315f43; text-decoration: underline; text-underline-offset: 3px; }
    .area-content { width: min(1000px, 90%); margin: auto; padding: 48px 0 80px; }
    .area-content h2 { margin: 38px 0 14px; color: #173e2e; font-size: clamp(25px, 3vw, 34px); }
    .area-content h3 { margin: 22px 0 8px; color: #173e2e; font-size: 19px; }
    .area-content p, .area-content li { color: #59665f; line-height: 1.8; }
    .area-content p + p { margin-top: 12px; }
    .area-image { margin: 28px 0; overflow: hidden; border-radius: 18px; background: #eef2eb; }
    .area-image img { width: 100%; height: auto; aspect-ratio: 16 / 9; object-fit: cover; }
    .area-links, .area-services { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin: 18px 0; }
    .area-links a, .area-links span, .area-services a { display: block; padding: 14px 16px; border: 1px solid #e3ebe6; border-radius: 12px; background: #fff; font-weight: 700; text-decoration: none; }
    .area-links a:hover, .area-services a:hover { background: #eaf5ee; }
    .area-faq { padding: 18px 20px; margin: 12px 0; border: 1px solid #e3ebe6; border-radius: 12px; background: #fff; }
    .area-cta { padding: 30px; margin-top: 38px; border-radius: 18px; background: #173e2e; color: #fff; }
    .area-cta h2, .area-cta p { color: #fff; }
    .area-cta-links { display: flex; flex-wrap: wrap; gap: 12px; margin-top: 20px; }
    .area-cta-links a { display: inline-flex; padding: 12px 18px; border-radius: 100px; background: #79b82a; color: #101610; font-weight: 800; text-decoration: none; }
    .area-cta-links a.secondary { background: #fff; }
    @media (max-width: 640px) { .area-content { padding-top: 34px; } .area-cta { padding: 22px; } }
</style>
"""
FAQ_DISCLOSURE_STYLE = """
<style>
    .area-faq { overflow: hidden; transition: border-color .2s ease, box-shadow .2s ease; }
    .area-faq:hover, .area-faq[open] { border-color: #79b82a; box-shadow: 0 8px 22px rgba(23, 62, 46, .09); }
    .area-faq summary { display: flex; align-items: center; justify-content: space-between; gap: 16px; padding: 18px 20px; color: #173e2e; font-weight: 700; cursor: pointer; list-style: none; }
    .area-faq summary::-webkit-details-marker { display: none; }
    .area-faq summary::after { content: "+"; flex: 0 0 28px; display: grid; width: 28px; height: 28px; place-items: center; border-radius: 50%; background: #eaf5ee; color: #315f43; font-size: 21px; line-height: 1; transition: transform .2s ease, background-color .2s ease; }
    .area-faq[open] summary::after { content: "−"; transform: rotate(180deg); background: #dcefdc; }
    .area-faq summary:focus-visible { outline: 3px solid #79b82a; outline-offset: -4px; }
    .area-faq-answer { padding: 0 20px 18px; animation: faq-reveal .24s ease-out; }
    .area-faq-answer p { margin: 0; }
    @keyframes faq-reveal { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }
    @media (prefers-reduced-motion: reduce) { .area-faq, .area-faq summary::after { transition: none; } .area-faq-answer { animation: none; } }
</style>
"""


def slugify(value: str) -> str:
    ascii_value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value).strip("-")
    if not slug:
        raise ValueError(f"Cannot make an ASCII URL slug from {value!r}")
    return slug


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def column_index(cell_ref: str) -> int:
    letters = re.match(r"[A-Z]+", cell_ref)
    if letters is None:
        raise ValueError(f"Invalid spreadsheet cell reference: {cell_ref}")
    index = 0
    for letter in letters.group():
        index = index * 26 + ord(letter) - ord("A") + 1
    return index - 1


def read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    try:
        xml_bytes = archive.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    root = ET.fromstring(xml_bytes)
    return [
        "".join(node.text or "" for node in item.iter(f"{{{SHEET_NS}}}t"))
        for item in root.findall(f"{{{SHEET_NS}}}si")
    ]


def workbook_sheet_path(archive: zipfile.ZipFile) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    first_sheet = workbook.find(f".//{{{SHEET_NS}}}sheet")
    if first_sheet is None:
        raise ValueError("The workbook contains no worksheets")
    relation_id = first_sheet.attrib.get(f"{{{DOC_REL_NS}}}id")
    relationship = next(
        (
            item
            for item in relations.findall(f"{{{PKG_REL_NS}}}Relationship")
            if item.attrib.get("Id") == relation_id
        ),
        None,
    )
    if relationship is None:
        raise ValueError("Could not resolve the workbook's first worksheet")
    target = relationship.attrib["Target"]
    return posixpath.normpath(
        target.lstrip("/") if target.startswith("/") else posixpath.join("xl", target)
    )


def read_workbook(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared = read_shared_strings(archive)
        sheet_root = ET.fromstring(archive.read(workbook_sheet_path(archive)))

    rows: list[list[str]] = []
    for row in sheet_root.findall(f".//{{{SHEET_NS}}}sheetData/{{{SHEET_NS}}}row"):
        values: list[str] = []
        cells = row.findall(f"{{{SHEET_NS}}}c")
        if not cells:
            continue
        max_column = max(column_index(cell.attrib["r"]) for cell in cells)
        values = [""] * (max_column + 1)
        for cell in cells:
            cell_type = cell.attrib.get("t")
            if cell_type == "inlineStr":
                value = "".join(
                    node.text or ""
                    for node in cell.iter(f"{{{SHEET_NS}}}t")
                )
            else:
                value_node = cell.find(f"{{{SHEET_NS}}}v")
                value = value_node.text if value_node is not None else ""
                if cell_type == "s" and value:
                    value = shared[int(value)]
            values[column_index(cell.attrib["r"])] = value.strip()
        rows.append(values)

    if not rows:
        raise ValueError("The workbook has no data rows")
    headers = {normalize_header(value): index for index, value in enumerate(rows[0])}
    columns = {
        "district": headers.get("district"),
        "area": headers.get("servicearea"),
        "title": headers.get("suggestedpagetitle"),
        "pin": headers.get("pincode"),
    }
    sr_no_column = headers.get("srno")
    missing_headers = [name for name, index in columns.items() if index is None]
    if missing_headers:
        raise ValueError(
            "Missing workbook columns: " + ", ".join(missing_headers)
        )

    result = []
    for row_number, values in enumerate(rows[1:], start=2):
        if not any(values):
            continue
        record = {
            name: values[index] if index < len(values) else ""
            for name, index in columns.items()
        }
        record["sr_no"] = (
            values[sr_no_column]
            if sr_no_column is not None and sr_no_column < len(values)
            else str(len(result) + 1)
        )
        if not record["district"] or not record["area"] or not record["title"]:
            raise ValueError(f"Workbook row {row_number} has a blank required value")
        result.append(record)
    validate_rows(result)
    return result


def validate_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        raise ValueError("The workbook contains no service-area rows")
    seen_area_keys: set[tuple[str, str]] = set()
    urls: set[str] = set()
    for row in rows:
        area_key = (row["district"].casefold(), row["area"].casefold())
        if area_key in seen_area_keys:
            raise ValueError(f"Duplicate area within district: {row['district']} / {row['area']}")
        seen_area_keys.add(area_key)
        url = area_url(row)
        if url in urls:
            raise ValueError(f"Duplicate generated URL: {url}")
        urls.add(url)


def assign_district_order(rows: list[dict[str, str]]) -> None:
    next_order: dict[str, int] = defaultdict(int)
    for row in rows:
        row["district_order"] = str(next_order[row["district"]])
        next_order[row["district"]] += 1


def district_directory_map() -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in ROOT.glob("pest-control-in-*"):
        if not path.is_dir():
            continue
        directory_slug = path.name.removeprefix("pest-control-in-").replace("_", "-")
        result[directory_slug] = path
    return result


def district_directory(district: str, directories: dict[str, Path]) -> Path:
    slug = slugify(district)
    slug = PARENT_ALIASES.get(slug, slug)
    if slug not in directories:
        raise ValueError(
            f"No existing district directory for {district!r}; expected its URL to stay unchanged"
        )
    return directories[slug]


def area_slug(row: dict[str, str]) -> str:
    area = slugify(row["area"])
    district = slugify(row["district"])
    district_suffix = f"-{district}"
    if area.endswith(district_suffix):
        return area[: -len(district_suffix)]
    return area


def area_url(row: dict[str, str], directories: dict[str, Path] | None = None) -> str:
    district_slug = slugify(row["district"])
    if directories is not None:
        directory = district_directory(row["district"], directories)
        district_slug = directory.name.removeprefix("pest-control-in-")
    return f"/pest-control-in-{district_slug}/{area_slug(row)}/"


def load_copy_data() -> dict:
    with COPY_FILE.open(encoding="utf-8") as file:
        data = json.load(file)
    if not data.get("copy_variants") or not data.get("faq_sets"):
        raise ValueError(f"{COPY_FILE} needs copy_variants and faq_sets")
    return data


def e(value: str) -> str:
    return html.escape(value, quote=True)


def fill(template: str, row: dict[str, str], siblings: list[dict[str, str]]) -> str:
    values = {
        **row,
        "siblings": ", ".join(item["area"] for item in siblings),
        "pin_context": (
            f"Our local pest control technicians cover PIN code {row['pin']} for "
            f"{row['area']}, {row['district']}."
            if row["pin"]
            else ""
        ),
    }
    return template.format_map(values)


def variation_seed(row: dict[str, str], purpose: str = "") -> int:
    key = f"{row['district'].casefold()}|{row['area'].casefold()}|{purpose}"
    return int.from_bytes(hashlib.sha256(key.encode("utf-8")).digest()[:4], "big")


def location_trust_section(
    row: dict[str, str], siblings: list[dict[str, str]]
) -> str:
    variants = {
        "dosage": [
            "Dosage and dilution decisions take account of surface conditions and pest biology.",
            "Surface conditions and pest biology guide dosage and dilution choices.",
            "Treatment planning considers the site surface, pest biology and appropriate dilution.",
            "We consider the surface and pest biology when discussing dosage and dilution.",
            "Dosage choices are based on the surface conditions and the pest involved.",
        ],
        "formulations": [
            "Formulation choices are discussed in relation to the agreed treatment requirements.",
            "The treatment plan explains the formulations selected for the service.",
            "Formulations are selected for the treatment and site requirements discussed during assessment.",
            "We explain the treatment products and their intended use before service.",
            "The proposed service includes a discussion of the formulations relevant to the treatment.",
        ],
        "root-cause": [
            "The linked services cover {pests}; assessment can consider possible entry routes and conditions behind reported activity.",
            "For the linked {pests} services, an assessment can look at access points and conditions associated with reported signs.",
            "The page links services for {pests}; a site discussion can include possible entry routes and related conditions.",
            "When discussing linked {pests} services, we can consider entry points and conditions related to reported activity.",
            "Reported signs related to linked {pests} services can be considered alongside possible entry routes and site conditions.",
        ],
    }
    area = e(row["area"])
    district = e(row["district"])
    credential = approved_claim("certificationWording")
    dosage = variants["dosage"][
        variation_seed(row, "trust-dosage") % len(variants["dosage"])
    ]
    formulation = variants["formulations"][
        variation_seed(row, "trust-formulations") % len(variants["formulations"])
    ]
    available_services = {label for label, _ in SERVICES}
    pest_services = (
        ("Termite Control", "termites"),
        ("Rodent Management", "rodents"),
        ("Bed Bug Eradication", "bed bugs"),
        ("Wood Borer Control", "wood borers"),
        ("Fly Management Systems", "flies"),
        ("Wasp & Hornet Nest Removal", "wasps and hornets"),
    )
    pests = ", ".join(
        pest for service, pest in pest_services if service in available_services
    )
    root_cause = variants["root-cause"][
        variation_seed(row, "trust-root-cause") % len(variants["root-cause"])
    ].format(pests=pests)

    area_type = row["area"].casefold()
    if re.search(r"\b(?:industrial area|factory|factories|warehouse|godown|food factory)\b", area_type):
        industrial = (
            f"For {area}, planning can account for factory or industrial-premises "
            "access and operating schedules."
        )
    elif re.search(r"\b(?:market|mandi)\b", area_type):
        industrial = (
            f"For {area}, planning can account for market-premises access and "
            "operating schedules."
        )
    elif re.search(r"\b(?:farm|dairy)\b", area_type):
        industrial = (
            f"For {area}, planning can account for farm-premises access and "
            "operating schedules."
        )
    else:
        industrial_variants = [
            f"For premises in {area}, service planning can account for site conditions and access.",
            f"At {area}, commercial requirements can be discussed around the premises and access needs.",
            f"Service planning for {area} can be discussed after reviewing the premises and operating needs.",
            f"For {area}, the service scope can be discussed in relation to site conditions and access.",
            f"Commercial pest-management needs in {area} can be discussed for the individual premises.",
        ]
        industrial = industrial_variants[
            variation_seed(row, "trust-industrial") % len(industrial_variants)
        ]

    nearby = [e(item["area"]) for item in siblings if item["area"]]
    pin = row.get("pin", "").strip()
    coverage = f"{area}, {district}"
    if pin:
        coverage += f" (PIN {e(pin)})"
    response = (
        f"Contact the team to discuss inspection availability in {coverage}"
        + (f" and nearby localities including {e(', '.join(nearby))}." if nearby else ".")
    )

    icons = [
        '<path d="M12 3 19 6v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3Z"/><path d="m9 12 2 2 4-4"/>',
        '<path d="M9 3h6"/><path d="M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><path d="M8 15h8"/>',
        '<path d="M12 3 20 6v5c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-3Z"/><path d="m9 12 2 2 4-4"/>',
        '<path d="M3 21V8l9-5 9 5v13"/><path d="M3 11h18"/><path d="M7 11v4h3v-4"/><path d="M14 11v4h3v-4"/><path d="M10 21v-5h4v5"/>',
        '<circle cx="11" cy="11" r="7"/><circle cx="11" cy="11" r="3"/><path d="m20 20-4-4"/>',
        '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    ]
    cards = [
        ("Calculated Dosage", dosage),
        ("Treatment Formulations", formulation),
        ("Industrial Compliance", industrial),
        ("Root-Cause Approach", root_cause),
        ("Rapid Response", response),
    ]
    if credential:
        cards.insert(0, ("Credentials", credential))
    cards_html = "\n".join(
        f"""<div class="location-card" style="background:#fff;padding:30px;border:1px solid #e4ebe6;border-radius:20px;box-shadow:0 12px 35px rgba(20,55,40,.06)">
                        <div class="location-icon" style="width:52px;height:52px;display:flex;align-items:center;justify-content:center;border-radius:14px;background:#eaf5ee;margin-bottom:18px"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#5d951b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">{icon}</svg></div>
                        <h3>{heading}</h3>
                        <p>{e(copy)}</p>
                    </div>"""
        for (heading, copy), icon in zip(cards, icons)
    )
    return f"""
            <section class="location-section" aria-labelledby="why-choose-us-heading">
                <h2 id="why-choose-us-heading">Why Choose Us</h2>
                <div class="location-grid">
                    {cards_html}
                </div>
            </section>"""


def normalized_text(fragment: str) -> str:
    text = re.sub(r"<script\b.*?</script>", " ", fragment, flags=re.I | re.S)
    text = re.sub(r"<style\b.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def get_area_detail(
    copy_data: dict, row: dict[str, str], *, required: bool
) -> dict | None:
    key = f"{row['district']}|{row['area']}"
    detail = copy_data.get("area_details", {}).get(key)
    if required and not detail:
        raise ValueError(
            f"Missing verified area-specific copy at area_details[{key!r}]"
        )
    return detail


def faq_items(
    row: dict[str, str], siblings: list[dict[str, str]], copy_data: dict, detail: dict | None
) -> list[dict[str, str]]:
    variants = copy_data["faq_sets"]
    item_index = variation_seed(row, "faq") % len(variants)
    templates = variants[item_index]["items"]
    items = [
        {
            "question": fill(item["question"], row, siblings),
            "answer": fill(item["answer"], row, siblings),
        }
        for item in templates
    ]
    if detail and detail.get("faqs"):
        items = [
            {
                "question": str(item["question"]).strip(),
                "answer": str(item["answer"]).strip(),
            }
            for item in detail["faqs"]
        ]
    elif detail is not None:
        raise ValueError(
            f"Verified area-specific FAQs are required for {row['area']}, {row['district']}"
        )
    if not 5 <= len(items) <= 6 or any(
        not item["question"] or not item["answer"] for item in items
    ):
        raise ValueError(f"Expected 5–6 complete visible FAQs for {row['area']}, {row['district']}")
    return items


def structured_data(
    row: dict[str, str], url: str, title: str, description: str, faqs: list[dict[str, str]]
) -> str:
    if load_site_claims().get("HOLD_BEAWAR", True) is True and row["district"].casefold() == "beawar":
        served_areas = [{"@type": "State", "name": "Rajasthan"}]
    else:
        served_areas = [
            {"@type": "Place", "name": row["area"]},
            {"@type": "AdministrativeArea", "name": row["district"]},
        ]
    data = {
        "@context": "https://schema.org",
        "@graph": [
            website_schema(),
            {
                "@type": "LocalBusiness",
                "@id": f"{BASE_URL}/#business",
                "name": "Super Pest Control Services",
                "url": f"{BASE_URL}/",
                "image": f"{BASE_URL}/images/logo.webp",
                "telephone": "+91-9828066990",
                "contactPoint": [
                    {"@type": "ContactPoint", "telephone": "+91-9828066990", "contactType": "customer service"},
                    {"@type": "ContactPoint", "telephone": "+91-7976572984", "contactType": "customer service"},
                ],
                "address": {
                    "@type": "PostalAddress",
                    "streetAddress": "82/270, Sector-8, Pratap Nagar, Sanganer",
                    "addressLocality": "Jaipur",
                    "addressRegion": "Rajasthan",
                    "postalCode": "302033",
                    "addressCountry": "IN",
                },
                "areaServed": served_areas,
            },
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": title,
                "description": description,
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "about": {"@id": f"{BASE_URL}/#business"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": "Service Locations", "item": f"{BASE_URL}/service-location/"},
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": row["district"],
                        "item": f"{BASE_URL}/pest-control-in-{district_path_slug(row['district'])}/",
                    },
                    {"@type": "ListItem", "position": 4, "name": row["area"], "item": url},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faqs
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def district_path_slug(district: str) -> str:
    slug = slugify(district)
    return PARENT_ALIASES.get(slug, slug).replace("-", "_") if slug in {
        "didwana-kuchaman",
        "khairthal-tijara",
        "kotputli-behror",
        "sawai-madhopur",
        "sri-ganganagar",
    } else PARENT_ALIASES.get(slug, slug)


def render_page(
    row: dict[str, str],
    rows: list[dict[str, str]],
    copy_data: dict,
    *,
    sample: bool,
) -> tuple[str, str, str]:
    directories = district_directory_map()
    url_path = area_url(row, directories)
    url = f"{BASE_URL}{url_path}"
    title = f"{row['area']} Pest Control | {row['district']}"
    pin_phrase = f" (PIN {row['pin']})" if row["pin"] else ""
    description = (
        f"Pest control serving {row['area']}, {row['district']}{pin_phrase}. "
        "Explore residential and commercial services, nearby areas and booking options."
    )
    if len(description) > 155:
        description = f"{row['area']}, {row['district']}{pin_phrase}: residential and commercial pest control. Contact our team."
    if len(description) > 155:
        raise ValueError(f"Meta description exceeds 155 characters for {row['area']}, {row['district']}")
    image_filename, image_alt = image_for_district(row["district"])
    image_url = f"{BASE_URL}/images/{image_filename}"
    index = next((i for i, item in enumerate(rows) if item is row), 0)
    same_district = [item for item in rows if item["district"] == row["district"] and item is not row]
    siblings = [
        same_district[(index + offset) % len(same_district)]
        for offset in range(min(5, len(same_district)))
    ] if same_district else []
    selected_variant = copy_data["copy_variants"][
        variation_seed(row, "intro") % len(copy_data["copy_variants"])
    ]
    override_key = f"{row['district']}|{row['area']}"
    page_override = copy_data.get("page_overrides", {}).get(override_key, {})
    detail = get_area_detail(copy_data, row, required=False)
    if detail is not None:
        intro_paragraphs = [str(text) for text in detail.get("intro", [])]
        residential_paragraphs = [str(text) for text in detail.get("residential_commercial", [])]
        process_paragraphs = [str(text) for text in detail.get("process", [])]
        amc_paragraphs = [str(text) for text in detail.get("amc", [])]
        nearby_paragraphs = [str(text) for text in detail.get("nearby_context", [])]
    else:
        coverage = copy_data.get("residential_commercial_variants", [])
        process = copy_data.get("process_variants", [])
        amc = copy_data.get("amc_variants", [])
        if not coverage or not process or not amc:
            raise ValueError("Residential, process, and AMC copy variant pools are required")
        intro_paragraphs = [fill(selected_variant["intro"], row, siblings)]
        residential_paragraphs = [
            coverage[variation_seed(row, "coverage") % len(coverage)].format(**row)
        ]
        process_paragraphs = [
            process[variation_seed(row, "process") % len(process)].format(**row)
        ]
        amc_paragraphs = [
            amc[variation_seed(row, "amc") % len(amc)].format(**row)
        ]
        nearby_paragraphs = [
            f"Our rapid-response teams also serve these nearby areas in {row['district']}: "
            + ", ".join(item["area"] for item in siblings)
            + ". Use the links below to explore their service pages."
        ]
    if detail:
        for field_name, values in (
            ("intro", intro_paragraphs),
            ("residential_commercial", residential_paragraphs),
            ("process", process_paragraphs),
            ("amc", amc_paragraphs),
            ("nearby_context", nearby_paragraphs),
        ):
            if not values or any(not value.strip() for value in values):
                raise ValueError(f"Verified copy field {field_name!r} is blank for {row['area']}, {row['district']}")

    faqs = faq_items(row, siblings, copy_data, detail)
    faqs_json = structured_data(row, url, title, description, faqs)
    breadcrumb_district_url = f"/pest-control-in-{district_path_slug(row['district'])}/"

    paragraph_html = lambda values: "\n".join(f"<p>{e(value)}</p>" for value in values)
    if sample:
        sibling_links = "\n".join(
            f'<span>Pest Control in {e(sibling["area"])}, {e(sibling["district"])}</span>'
            for sibling in siblings
        )
        nearby_paragraphs = [
            f"The workbook also lists {', '.join(item['area'] for item in siblings)} in {row['district']}. "
            "Dedicated sibling-page links will be enabled when the complete area set is approved."
        ]
    else:
        sibling_links = "\n".join(
            f'<a href="{e(area_url(sibling, directories))}">Pest Control in {e(sibling["area"])}, {e(sibling["district"])}</a>'
            for sibling in siblings
        )
    guides = copy_data.get("general_guides", [])
    if len(guides) < 2:
        raise ValueError("At least two general_guides are required for area pages")
    guide_indexes = (
        variation_seed(row, "guide-primary") % len(guides),
        variation_seed(row, "guide-secondary") % len(guides),
    )
    if guide_indexes[0] == guide_indexes[1]:
        guide_indexes = (guide_indexes[0], (guide_indexes[1] + 1) % len(guides))
    if guide_indexes[0] == guide_indexes[1]:
        raise ValueError("The selected general pest-control guides must be distinct")
    guide_html = "\n".join(
        f"""<section aria-labelledby="guide-{guide_index}-heading">
            <h3 id="guide-{guide_index}-heading">{e(guides[guide_index]["title"])}</h3>
            {paragraph_html([str(text) for text in guides[guide_index]["paragraphs"]])}
        </section>"""
        for guide_index in guide_indexes
    )
    services_html = "\n".join(
        f'<a href="{path}">{e(label)}</a>' for label, path in SERVICES
    )
    overlap_pages_file = ROOT / "data" / "overlap-flagged-pages.json"
    flagged_pages = (
        set(json.loads(overlap_pages_file.read_text(encoding="utf-8")))
        if overlap_pages_file.exists()
        else set()
    )
    local_notes_file = ROOT / "local_notes_template.csv"
    area_key = f"{row['district']}|{row['area']}"
    local_note = {}
    if local_notes_file.exists():
        import csv

        with local_notes_file.open(encoding="utf-8-sig", newline="") as notes_stream:
            local_note = next(
                (
                    note for note in csv.DictReader(notes_stream)
                    if f"{note.get('district', '').strip()}|{note.get('area', '').strip()}" == area_key
                ),
                {},
            )
    has_local_notes = any(
        local_note.get(field, "").strip()
        for field in (
            "landmarks_or_known_places",
            "typical_property_types",
            "pests_commonly_seen",
            "seasonal_notes",
            "real_job_example",
        )
    )
    page_key = url_path.lstrip("/").rstrip("/") + "/index.html"
    if page_key in flagged_pages:
        trust_section = ""
    else:
        trust_section = location_trust_section(row, siblings)

    local_note_lines = []
    if local_note.get("landmarks_or_known_places", "").strip():
        local_note_lines.append(
            f"<p>The supplied notes identify {e(local_note['landmarks_or_known_places'].strip())} "
            "as nearby places.</p>"
        )
    if local_note.get("typical_property_types", "").strip():
        local_note_lines.append(
            f"<p>The property types recorded in the notes are "
            f"{e(local_note['typical_property_types'].strip())}.</p>"
        )
    if local_note.get("pests_commonly_seen", "").strip():
        local_note_lines.append(
            f"<p>The pests recorded in the notes are "
            f"{e(local_note['pests_commonly_seen'].strip())}.</p>"
        )
    if local_note.get("seasonal_notes", "").strip():
        local_note_lines.append(
            f"<p>The seasonal observations provided are "
            f"{e(local_note['seasonal_notes'].strip())}.</p>"
        )
    if local_note.get("real_job_example", "").strip():
        local_note_lines.append(
            f"<p>The verified job example provided is "
            f"{e(local_note['real_job_example'].strip())}.</p>"
        )
    local_notes_section = (
        '<section aria-labelledby="local-situations-heading">'
        '<h2 id="local-situations-heading">Local situations we handle</h2>'
        + "\n".join(local_note_lines)
        + "</section>"
        if local_note_lines
        else ""
    )
    if page_override.get("interactive_faqs"):
        faq_html = "\n".join(
            f'<details class="area-faq"><summary>{e(item["question"])}</summary>'
            f'<div class="area-faq-answer"><p>{e(item["answer"])}</p></div></details>'
            for item in faqs
        )
        faq_style = FAQ_DISCLOSURE_STYLE
    else:
        faq_html = "\n".join(
            f'<article class="area-faq"><h3>{e(item["question"])}</h3><p>{e(item["answer"])}</p></article>'
            for item in faqs
        )
        faq_style = ""
    equipment_question = (
        f"Will pest-control spraying leave stains or puddles on floors in "
        f"{e(row['area'])}?"
    )
    equipment_answer = (
        "Technicians can use automated constant-pressure electric sprayers "
        "for perimeter coverage and precision manual compression sprayers "
        "for targeted indoor crack-and-crevice work. The equipment and "
        "application volume are selected for the surface and site; careful "
        "application is intended to reduce splashing and excess wetting, "
        "though no method can guarantee a completely mark-free result on "
        "every finish. Ask about property-specific preparation and aftercare."
    )
    if page_override.get("interactive_faqs"):
        faq_html += (
            f'<details class="area-faq"><summary>{equipment_question}</summary>'
            f'<div class="area-faq-answer"><p>{e(equipment_answer)}</p></div></details>'
        )
    else:
        faq_html += (
            f'<article class="area-faq"><h3>{equipment_question}</h3>'
            f'<p>{e(equipment_answer)}</p></article>'
        )
    image_width = page_override.get("image_width")
    image_style = f' style="width: {e(str(image_width))}; margin-inline: auto;"' if image_width else ""
    section_blocks = {
        "residential_commercial": f"""
            <section aria-labelledby="residential-commercial-heading">
                <h2 id="residential-commercial-heading">Residential and commercial coverage</h2>
                {paragraph_html(residential_paragraphs)}
            </section>""",
        "process": f"""
            <section aria-labelledby="process-heading">
                <h2 id="process-heading">How the service process works</h2>
                {paragraph_html(process_paragraphs)}
            </section>""",
        "amc": f"""
            <section aria-labelledby="amc-heading">
                <h2 id="amc-heading">Commercial AMC and IPM plans</h2>
                {paragraph_html(amc_paragraphs)}
                <p>Learn about <a href="/services/commercial-amc-ipm/">Commercial AMC (IPM)</a> or <a href="/contact/">contact our team</a> to discuss a property assessment.</p>
            </section>""",
        "nearby_context": f"""
            <section aria-labelledby="nearby-areas-heading">
                <h2 id="nearby-areas-heading">Nearby service areas in {e(row['district'])}</h2>
                {paragraph_html(nearby_paragraphs)}
                <div class="area-links">{sibling_links}</div>
                <p><a href="{e(breadcrumb_district_url)}">More areas in {e(row['district'])}</a></p>
            </section>""",
    }
    orders = copy_data.get("section_orders", [])
    order_index = variation_seed(row, "section-order") % len(orders) if orders else 0
    section_order = orders[order_index] if orders else list(section_blocks)
    if set(section_order) != set(section_blocks):
        raise ValueError("Each section_orders entry must contain all supported sections exactly once")
    ordered_sections = "\n".join(section_blocks[name] for name in section_order)
    breadcrumb = f"""
    <nav class="area-breadcrumb" aria-label="Breadcrumb">
        <ol>
            <li><a href="/">Home</a></li>
            <li><a href="/service-location/">Service Locations</a></li>
            <li><a href="{e(breadcrumb_district_url)}">{e(row['district'])}</a></li>
            <li aria-current="page">{e(row['area'])}</li>
        </ol>
    </nav>"""
    meta_robots = '<meta name="robots" content="noindex,follow">' if sample else ""
    pin_line = (
        f"<p>Serving {e(row['area'])}, {e(row['district'])} — PIN code {e(row['pin'])}.</p>"
        if row["pin"]
        else ""
    )
    pin_data_paragraph = (
        f"<p>Our local pest control technicians cover PIN code <strong>{e(row['pin'])}</strong> "
        f"for {e(row['area'])}, {e(row['district'])}.</p>"
        if row["pin"]
        else ""
    )
    escaped_json = faqs_json.replace("</", "<\\/")
    schema_script = f'<script type="application/ld+json">{escaped_json}</script>'
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}">
    <link rel="canonical" href="{e(url)}">
    {meta_robots}
    <meta property="og:type" content="website">
    <meta property="og:title" content="{e(title)}">
    <meta property="og:description" content="{e(description)}">
    <meta property="og:url" content="{e(url)}">
    <meta property="og:image" content="{image_url}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{e(title)}">
    <meta name="twitter:description" content="{e(description)}">
    <meta name="twitter:image" content="{image_url}">
    {schema_script}
    <link rel="icon" type="image/webp" href="/images/Logooo.webp">
    <link rel="preload" href="/css/style.min.css" as="style" fetchpriority="high" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="/css/style.min.css"></noscript>
    {AREA_STYLE}
    {faq_style}
</head>
<body>
    <!-- GENERATED AREA PAGE: {url_path} -->
    <header class="header">
        <nav class="navbar" aria-label="Main navigation">
            <a href="/" class="logo">
                <div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" loading="eager" alt="Super Pest Control Services"></div>
                <div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div>
            </a>
            <div class="nav-links">
                <a href="/">Home</a><a href="/services/">Services</a>
                <a href="/residential-pest-control/">Residential</a>
                <a href="/commercial-pest-control/">Commercial</a><a href="/about/">About</a>
                <a href="/blog/">Blogs</a><a href="/service-location/" class="active">Service Location</a>
                <a href="/contact/">Contact</a>
            </div>
            <a href="/contact/" class="nav-btn">Book Service</a>
            <button class="menu-btn" id="menuBtn" type="button" aria-label="Open navigation menu">☰</button>
        </nav>
    </header>
    <main class="area-main">
        <section class="page-hero">
            <span>PEST CONTROL • {e(row['district'].upper())}</span>
            <h1>Pest Control in {e(row['area'])}, {e(row['district'])}</h1>
            {pin_line}
            <div class="area-cta-links" style="justify-content:center">
                <a href="tel:+919828066990">Call +91 98280-66990</a>
                <a href="tel:+917976572984" class="secondary">Call +91 79765-72984</a>
                <a href="https://wa.me/917976572984" class="secondary" target="_blank" rel="noopener">WhatsApp</a>
            </div>
        </section>
        {breadcrumb}
        <article class="area-content">
            <figure class="area-image"{image_style}>
                <img src="/images/{image_filename}" alt="{e(image_alt)}" width="1200" height="675" loading="eager" decoding="async" fetchpriority="high">
            </figure>
            <section aria-labelledby="area-intro-heading">
                <h2 id="area-intro-heading">Pest control serving {e(row['area'])}</h2>
                {paragraph_html(intro_paragraphs)}
                {pin_data_paragraph}
            </section>
            <section aria-labelledby="area-services-heading">
                <h2 id="area-services-heading">Services available to request</h2>
                <p>Explore the individual service pages to understand the treatment scope and request an assessment for your property.</p>
                <div class="area-services">{services_html}</div>
            </section>
            {trust_section}
            {local_notes_section}
            <section aria-labelledby="practical-guidance-heading">
                <h2 id="practical-guidance-heading">Practical pest-control guidance</h2>
                {guide_html}
            </section>
            {ordered_sections}
            <section aria-labelledby="faq-heading">
                <h2 id="faq-heading">Frequently asked questions</h2>
                {faq_html}
            </section>
            <section class="area-cta" aria-labelledby="contact-heading">
                <h2 id="contact-heading">Request pest control in {e(row['area'])}</h2>
                <p>Contact Super Pest Control Services to discuss an inspection or service request for {e(row['area'])}, {e(row['district'])}.</p>
                <div class="area-cta-links">
                    <a href="tel:+919828066990">Call +91 98280-66990</a>
                    <a href="tel:+917976572984" class="secondary">Call +91 79765-72984</a>
                    <a href="https://wa.me/917976572984" class="secondary" target="_blank" rel="noopener">WhatsApp our team</a>
                    <a href="/contact/" class="secondary">Book an inspection</a>
                </div>
            </section>
        </article>
    </main>
    <footer class="footer">
        <div class="footer-grid">
            <div class="footer-brand">
                <a href="/" class="logo">
                    <div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" loading="lazy" alt="Super Pest Control Services"></div>
                    <div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div>
                </a>
                <p>{e(approved_claim("experienceWording") or "Pest management services for homes, businesses and institutions.")}</p>
                <div class="social-links" aria-label="Social media links">
                    <a href="https://www.instagram.com/superpestcontrolservices?igsh=YzM3cmN0b2EwdGxh" target="_blank" rel="noopener" aria-label="Instagram">
                        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"></rect><circle cx="12" cy="12" r="4"></circle><circle cx="17.5" cy="6.5" r="1"></circle></svg>
                    </a>
                    <a href="https://x.com/Superpestcontro" target="_blank" rel="noopener" aria-label="X">
                        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 4l14 16M19 4L5 20"></path></svg>
                    </a>
                    <a href="https://www.facebook.com/p/Super-Pest-Control-Services-100075474775254/" target="_blank" rel="noopener" aria-label="Facebook">
                        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M14 21v-8h3l.5-3H14V8.2c0-.9.3-1.5 1.6-1.5H18V4.1c-.4-.1-1.3-.2-2.4-.2-2.4 0-4.1 1.5-4.1 4.2V10H9v3h2.5v8"></path></svg>
                    </a>
                    <a href="https://www.linkedin.com/in/kishor-singh-10866a252/" target="_blank" rel="noopener" aria-label="LinkedIn">
                        <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 8v11M5 5.2v.1M10 19v-6.2a3 3 0 0 1 6 0V19M10 11v8M16 19v-6.2"></path></svg>
                    </a>
                </div>
            </div>
            <div class="footer-column"><h3>Quick Links</h3>
                <a href="/">Home</a><a href="/services/">Services</a>
                <a href="/about/">About</a><a href="/blog/">Blog</a>
                <a href="/service-location/">Service Location</a><a href="/contact/">Contact</a>
                <!-- BEGIN GENERATED LEGAL FOOTER LINKS --><a href="/privacy-policy/">Privacy Policy</a><a href="/terms-and-conditions/">Terms &amp; Conditions</a><!-- END GENERATED LEGAL FOOTER LINKS -->
            </div>
            <div class="footer-column"><h3>Services</h3>
                <a href="/services/ant-control/">Ant Control</a>
                <a href="/services/pre-construction-anti-termite-treatment/">Pre-Construction Anti-Termite Treatment</a>
                <a href="/services/termite-piping-system/">Termite Piping System</a>
                <a href="/services/termite-control/">Termite Treatment</a>
                <a href="/services/wood-borer-control/">Wood Borer Control</a>
                <a href="/services/general-pest-control/">General Pest Control (GPC)</a>
                <a href="/services/cockroach-control/">Cockroach Control</a>
                <a href="/services/rodent-management/">Rodent Management</a>
                <a href="/services/vector-control-fogging/">Vector Control &amp; Fogging</a>
                <a href="/services/bed-bug-eradication/">Bed Bug Eradication</a>
                <a href="/services/commercial-fumigation/">Commercial Fumigation</a>
                <a href="/services/fly-management-systems/">Fly Management Systems</a>
                <a href="/services/sanitization-disinfection/">Sanitization &amp; Disinfection</a>
                <a href="/services/commercial-amc-ipm/">Commercial AMC (IPM)</a>
                <a href="/services/wasp-hornet-nest-removal/">Wasp &amp; Hornet Nest Removal</a>
                <a href="/contact/">Any Other Pests?</a>
            </div>
            <div class="footer-column"><h3>Contact</h3>
                <p>+91 98280 66990</p><p>+91 79765 72984</p>
                <p>superpestcontrolservices.jaipur@gmail.com</p>
                <p>Jaipur, Rajasthan</p>
            </div>
        </div>
        <div class="footer-bottom"><p>© 2026 Super Pest Control Services. All Rights Reserved.</p></div>
    </footer>
    <a href="https://wa.me/917976572984" class="whatsapp" target="_blank" rel="noopener" aria-label="Chat on WhatsApp">
        <span>whatsapp</span>
    </a>
    <script src="/js/script.min.js?v=20260906" defer></script>
</body>
</html>
"""
    page = apply_main_footer(page)
    main_text = normalized_text(page.split("<main", 1)[1].split("</main>", 1)[0])
    word_count = len(re.findall(r"\b[\w'-]+\b", main_text))
    return page, url_path, main_text


def require_owned_or_missing(path: Path) -> None:
    if path.exists() and PAGE_MARKER not in path.read_text(encoding="utf-8"):
        raise ValueError(f"Refusing to overwrite a page not created by this generator: {path}")


def matching_div_end(text: str, start: int) -> int:
    tags = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)
    depth = 0
    for match in tags.finditer(text, start):
        if match.group().lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return match.end()
        else:
            depth += 1
    raise ValueError("Unclosed div while locating a district area grid")


def find_district_area_grid(page: str, district_path: Path) -> tuple[int, int, re.Match[str]]:
    headings = list(re.finditer(r"(?is)<h[23]\b[^>]*>.*?</h[23]\s*>", page))
    grid_pattern = re.compile(r"<div\b[^>]*>", re.I)
    for opening in grid_pattern.finditer(page):
        class_match = re.search(r"""class=["']([^"']*)["']""", opening.group(), re.I)
        if not class_match or "area-grid" not in class_match.group(1).split():
            continue
        if "generated-area-shell" in class_match.group(1).split():
            continue
        end = matching_div_end(page, opening.start())
        grid_text = page[opening.start():end]
        managed = AREA_LINKS_START in grid_text and AREA_LINKS_END in grid_text
        prior_headings = [
            heading for heading in headings
            if heading.end() <= opening.start()
            and re.search(
                r"(?is)(nearby\s+areas|areas?\s*&\s*pin|pin\s+codes?\s+we\s+serve|areas?\s+we\s+serve)",
                re.sub(r"<[^>]+>", " ", heading.group()),
            )
        ]
        if managed or prior_headings:
            if not managed and prior_headings:
                card_matches = re.search(
                    r"""<(?:div|a)\b[^>]*class=["'][^"']*\b(?:area-card|area-box)\b[^"']*["']""",
                    grid_text,
                    re.I,
                )
                if not card_matches:
                    continue
            return opening.start(), end, opening
    raise ValueError(f"Could not find the existing area-card grid in {district_path}")


def clean_legacy_area_name(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value))
    value = value.replace("\ufffd", " ").replace("�", " ")
    value = re.sub(r"[^\w\s.,'()/&+-]", " ", value)
    value = re.sub(r"\bPIN(?:\s+Code)?\s*:?\s*\d{5,6}\b", " ", value, flags=re.I)
    value = re.sub(r"\b\d{5,6}\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" ,;|&-/")
    return value


def normalized_area_name(value: str) -> str:
    value = clean_legacy_area_name(value)
    value = re.sub(r"\s*\([^)]*\)\s*", " ", value)
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def extract_legacy_card_names(grid_text: str) -> list[str]:
    names = []
    cards = re.finditer(
        r"""<(?:div|a)\b[^>]*class=["'][^"']*\b(?:area-card|area-box)\b[^"']*["'][^>]*>(.*?)</(?:div|a)\s*>""",
        grid_text,
        re.I | re.S,
    )
    for card in cards:
        strong = re.search(r"(?is)<strong\b[^>]*>(.*?)</strong\s*>", card.group(1))
        card_body = strong.group(1) if strong else re.sub(
            r"(?is)<(?:small|span)\b[^>]*>.*?</(?:small|span)\s*>",
            " ",
            card.group(1),
        )
        name = clean_legacy_area_name(card_body)
        if name:
            names.append(name)
    return names


def unmatched_name_list(
    names: list[str], area_rows: list[dict[str, str]]
) -> list[str]:
    workbook_names = {normalized_area_name(row["area"]) for row in area_rows}
    unmatched: list[str] = []
    seen: set[str] = set()
    for card_name in names:
        card_name = clean_legacy_area_name(card_name)
        whole = normalized_area_name(card_name)
        if whole in workbook_names:
            continue
        parts = [
            clean_legacy_area_name(part)
            for part in re.split(r"\s*/\s*|,\s*|\s*&\s*|\s+\band\b\s+", card_name, flags=re.I)
        ]
        matched_parts = [part for part in parts if normalized_area_name(part) in workbook_names]
        candidates = [part for part in parts if normalized_area_name(part) not in workbook_names]
        if not matched_parts or len(candidates) == len(parts):
            candidates = [card_name]
        for candidate in candidates:
            key = normalized_area_name(candidate)
            if key and key not in seen:
                seen.add(key)
                unmatched.append(candidate)
    return unmatched


def unmatched_legacy_names(grid_text: str, area_rows: list[dict[str, str]]) -> list[str]:
    return unmatched_name_list(extract_legacy_card_names(grid_text), area_rows)


def render_area_cards(
    district: str,
    area_rows: list[dict[str, str]],
    directories: dict[str, Path],
    card_class: str,
) -> str:
    cards = []
    for row in area_rows:
        title = f'Pest Control in {row["area"]}, {district}'
        if card_class == "area-box":
            pin_badge = f'<small>PIN {e(row["pin"])}</small>' if row["pin"] else ""
            body = f'{e(row["area"])}{pin_badge}'
        else:
            pin_badge = f'<span>PIN {e(row["pin"])}</span>' if row["pin"] else ""
            body = f'<strong>{e(row["area"])}</strong>{pin_badge}'
        cards.append(
            f'<a class="{e(card_class)} district-area-link" href="{e(area_url(row, directories))}" '
            f'title="{e(title)}">{body}</a>'
        )
    return AREA_LINKS_START + "\n" + "\n".join(cards) + "\n" + AREA_LINKS_END


def render_legacy_note(names: list[str]) -> str:
    if not names:
        return ""
    stored_names = e(json.dumps(names, ensure_ascii=False))
    visible_names = ", ".join(e(name) for name in names)
    return (
        f'{LEGACY_NOTE_START}<p class="legacy-area-note" data-legacy-names="{stored_names}">'
        f'<small>Other names from the previous list that are not separate Excel service areas: '
        f'{visible_names}. Contact us to confirm service availability.</small></p>{LEGACY_NOTE_END}'
    )


def matching_json_array_end(text: str, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "[":
            depth += 1
        elif char == "]":
            depth -= 1
            if depth == 0:
                return index + 1
    raise ValueError("Unclosed areaServed array in district schema")


def update_district_area_served(
    page: str, district: str, area_rows: list[dict[str, str]]
) -> str:
    script_pattern = re.compile(
        r'(<script type="application/ld\+json">)(.*?)(</script>)',
        re.I | re.S,
    )
    for match in script_pattern.finditer(page):
        script = match.group(2)
        data = json.loads(script.replace("<\\/", "</"))
        if not isinstance(data, dict) or "areaServed" not in data:
            continue
        served = data["areaServed"]
        if not isinstance(served, list):
            raise ValueError("Expected district areaServed schema to be an array")
        if load_site_claims().get("HOLD_BEAWAR", True) is True and district.casefold() == "beawar":
            filtered = [
                item for item in served
                if "beawar" not in json.dumps(item, ensure_ascii=False).casefold()
            ]
            if filtered == served:
                return page
            data["areaServed"] = filtered
            updated_script = json.dumps(data, ensure_ascii=False, indent=2)
            return page[:match.start(2)] + "\n" + updated_script + "\n" + page[match.end(2):]
        existing_names = {
            normalized_area_name(item.get("name", "") if isinstance(item, dict) else str(item))
            for item in served
        }
        additions = [
            {"@type": "Place", "name": f'{row["area"]}, {district}'}
            for row in area_rows
            if normalized_area_name(f'{row["area"]}, {district}') not in existing_names
        ]
        if not additions:
            return page

        array_match = re.search(r'"areaServed"\s*:\s*\[', script)
        if not array_match:
            raise ValueError("Could not locate areaServed array in district schema")
        array_start = array_match.end() - 1
        array_end = matching_json_array_end(script, array_start)
        raw_array = script[array_start:array_end]
        body = raw_array[1:-1]
        existing_body = body.rstrip()
        trailing_whitespace = body[len(existing_body):]
        indentation_match = re.search(r"\n([ \t]+)\S", raw_array)
        item_indent = indentation_match.group(1) if indentation_match else "                "
        encoded_additions = ",\n".join(
            item_indent
            + json.dumps(item, ensure_ascii=False, separators=(", ", ": "))
            for item in additions
        )
        if existing_body:
            updated_array = (
                "[" + existing_body + ",\n" + encoded_additions
                + trailing_whitespace + "]"
            )
        else:
            updated_array = "[" + "\n" + encoded_additions + trailing_whitespace + "]"
        updated_script = (
            script[:array_start] + updated_array + script[array_end:]
        )
        return (
            page[:match.start(2)] + updated_script + page[match.end(2):]
        )
    return page


def update_district_page(
    district_path: Path,
    district: str,
    area_rows: list[dict[str, str]],
    directories: dict[str, Path],
) -> list[str]:
    page = district_path.read_text(encoding="utf-8")
    page = update_district_area_served(page, district, area_rows)
    section_start = page.find(AREA_MARKER_START)
    section_end = page.find(AREA_MARKER_END)
    if (section_start == -1) != (section_end == -1):
        raise ValueError(f"Unbalanced generated area markers in {district_path}")
    if section_start >= 0:
        page = page[:section_start] + page[section_end + len(AREA_MARKER_END):]

    grid_start, grid_end, grid_opening = find_district_area_grid(page, district_path)
    grid_text = page[grid_start:grid_end]
    existing_note = re.search(
        rf"{re.escape(LEGACY_NOTE_START)}(.*?){re.escape(LEGACY_NOTE_END)}",
        page,
        re.S,
    )
    if existing_note:
        data_match = re.search(r"""data-legacy-names=["']([^"']*)["']""", existing_note.group(1))
        if not data_match:
            raise ValueError(f"Could not read retained legacy names in {district_path}")
        saved_names = json.loads(html.unescape(data_match.group(1)))
        legacy_names = unmatched_name_list(saved_names, area_rows)
        page = page[:existing_note.start()] + page[existing_note.end():]
        grid_start, grid_end, grid_opening = find_district_area_grid(page, district_path)
        grid_text = page[grid_start:grid_end]
    else:
        legacy_names = unmatched_legacy_names(grid_text, area_rows)

    card_match = re.search(
        r"""<(?:div|a)\b[^>]*class=["']([^"']*\b(area-card|area-box)\b[^"']*)["']""",
        grid_text,
        re.I,
    )
    card_class = card_match.group(2) if card_match else "area-card"
    updated_grid_opening = grid_opening.group()
    class_match = re.search(r"""class=(["'])(.*?)\1""", updated_grid_opening, re.I)
    if class_match:
        classes = class_match.group(2).split()
        if "district-area-grid" not in classes:
            classes.append("district-area-grid")
        updated_grid_opening = (
            updated_grid_opening[:class_match.start(2)]
            + " ".join(classes)
            + updated_grid_opening[class_match.end(2):]
        )
    updated_grid = (
        updated_grid_opening
        + "\n"
        + render_area_cards(district, area_rows, directories, card_class)
        + "\n</div>"
    )
    page = (
        page[:grid_start] + updated_grid + page[grid_end:]
    )
    grid_start, grid_end, grid_opening = find_district_area_grid(page, district_path)

    heading_matches = [
        heading for heading in re.finditer(r"(?is)<h[23]\b([^>]*)>(.*?)</h[23]\s*>", page[:grid_start])
        if re.search(
            r"(?is)(nearby\s+areas|areas?\s*&\s*pin|pin\s+codes?\s+we\s+serve|areas?\s+we\s+serve)",
            re.sub(r"<[^>]+>", " ", heading.group(2)),
        )
    ]
    if not heading_matches:
        raise ValueError(f"Could not find the area-list heading in {district_path}")
    heading = heading_matches[-1]
    page = (
        page[:heading.start()]
        + f"<h2{heading.group(1)}>Areas We Serve in {e(district)}</h2>"
        + page[heading.end():]
    )
    grid_start, grid_end, _ = find_district_area_grid(page, district_path)
    heading_matches = [
        heading for heading in re.finditer(r"(?is)<h[23]\b[^>]*>.*?</h[23]\s*>", page[:grid_start])
        if re.search(r"(?is)Areas We Serve", heading.group())
    ]
    intro_start = heading_matches[-1].end()
    intro_match = re.search(r"(?is)<p\b([^>]*)>.*?</p\s*>", page[intro_start:grid_start])
    intro = f"<p{intro_match.group(1) if intro_match else ''}>Choose your area in {e(district)} to see local pest control details.</p>"
    if intro_match:
        match_start = intro_start + intro_match.start()
        match_end = intro_start + intro_match.end()
        page = page[:match_start] + intro + page[match_end:]
    else:
        page = page[:intro_start] + intro + page[intro_start:]

    grid_start, grid_end, _ = find_district_area_grid(page, district_path)
    grid_close = page.rfind("</div>", grid_start, grid_end)
    if grid_close < 0:
        raise ValueError(f"Could not find closing area-grid tag in {district_path}")
    after_grid = grid_close + len("</div>")
    style = """<style>
    .area-grid.district-area-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .area-grid.district-area-grid .district-area-link { box-sizing: border-box; display: flex; align-items: center; justify-content: space-between; gap: 12px; color: #173e2e; text-decoration: none; }
    .area-grid.district-area-grid .district-area-link:hover { background: #eaf5ee; }
    .area-grid.district-area-grid .district-area-link:focus-visible { outline: 3px solid #1f6846; outline-offset: 3px; }
    .area-grid.district-area-grid .district-area-link small { color: #6c7872; }
    .legacy-area-note { margin-top: 14px; color: #59665f; line-height: 1.6; }
    @media (max-width: 600px) { .area-grid.district-area-grid { grid-template-columns: 1fr; } }
</style>"""
    style_matches = (
        match for match in re.finditer(r"(?is)<style\b[^>]*>.*?</style>", page[after_grid:])
        if ".district-area-link:hover" in match.group()
    )
    style_match = next(style_matches, None)
    if style_match:
        page = page[:after_grid] + page[after_grid + style_match.end():]
    note = render_legacy_note(legacy_names)
    page = page[:after_grid] + style + note + page[after_grid:]
    district_path.write_text(page, encoding="utf-8")
    return legacy_names


def update_sitemap(
    url_paths: list[str],
    districts: list[str],
    directories: dict[str, Path],
    changed_paths: set[str],
) -> None:
    ET.register_namespace("", SITEMAP_NS)
    root = ET.parse(SITEMAP_FILE).getroot()
    locations = {
        item.findtext(f"{{{SITEMAP_NS}}}loc"): item
        for item in root.findall(f"{{{SITEMAP_NS}}}url")
    }
    expected_paths = list(url_paths)
    expected_paths.extend(
        f"/{district_directory(district, directories).name}/" for district in districts
    )
    today = date.today().isoformat()
    for path in dict.fromkeys(expected_paths):
        location = f"{BASE_URL}{path}"
        item = locations.get(location)
        is_new = item is None
        if item is None:
            item = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
            ET.SubElement(item, f"{{{SITEMAP_NS}}}loc").text = location
        if is_new or path in changed_paths:
            lastmod = item.find(f"{{{SITEMAP_NS}}}lastmod")
            if lastmod is None:
                lastmod = ET.SubElement(item, f"{{{SITEMAP_NS}}}lastmod")
            lastmod.text = today
        locations[location] = item
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(SITEMAP_FILE, encoding="UTF-8", xml_declaration=True)


def validate_page_links(
    page: str, generated_paths: set[str], *, page_name: str
) -> None:
    for target in re.findall(r"""href=["']([^"'#]+)["']""", page):
        if target.startswith(("https://", "http://", "tel:", "mailto:", "sms:")):
            continue
        path = urlsplit(target).path
        if not path.startswith("/"):
            continue
        if path in generated_paths:
            continue
        local = ROOT / path.lstrip("/")
        if local.is_dir():
            local = local / "index.html"
        elif not local.suffix:
            local = local / "index.html"
        if not local.is_file():
            raise ValueError(f"Broken internal link in {page_name}: {target}")


def validate_bulk_pages(pages: list[tuple[dict[str, str], str, str, str]]) -> list[tuple[str, str, str, float]]:
    titles: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    h1s: dict[str, str] = {}
    paths: set[str] = set()
    generated_paths = {url_path for _, _, url_path, _ in pages}
    district_text: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for row, page, url_path, main_text in pages:
        title = re.search(r"<title>(.*?)</title>", page, re.S)
        description = re.search(r'<meta name="description" content="([^"]*)"', page)
        heading = re.search(r"<h1>(.*?)</h1>", page, re.S)
        if not title or not description or not heading:
            raise ValueError(f"Missing SEO title, description or H1: {url_path}")
        title_text = normalized_text(title.group(1))
        description_text = html.unescape(description.group(1))
        h1_text = normalized_text(heading.group(1))
        for collection, value, label in (
            (titles, title_text, "title"),
            (descriptions, description_text, "meta description"),
            (h1s, h1_text, "H1"),
        ):
            if value in collection:
                raise ValueError(
                    f"Duplicate {label} in {url_path} and {collection[value]}"
                )
            collection[value] = url_path
        if url_path in paths:
            raise ValueError(f"Duplicate canonical URL: {url_path}")
        paths.add(url_path)
        if len(re.findall(r"<h1(?:\s|>)", page, re.I)) != 1:
            raise ValueError(f"Expected exactly one H1: {url_path}")
        scripts = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', page, re.S
        )
        if len(scripts) != 1:
            raise ValueError(f"Expected one JSON-LD script: {url_path}")
        json.loads(scripts[0].replace("<\\/", "</"))
        if len(re.findall(r"<a\s", page, re.I)) < 4:
            raise ValueError(f"Expected at least four internal links: {url_path}")
        validate_page_links(page, generated_paths, page_name=url_path)
        district_text[row["district"]].append((url_path, main_text))

    similar_pairs = []
    for district, items in district_text.items():
        for index, (left_url, left_text) in enumerate(items):
            for right_url, right_text in items[index + 1:]:
                similarity = difflib.SequenceMatcher(
                    None, left_text.casefold(), right_text.casefold()
                ).ratio()
                if similarity > 0.60:
                    similar_pairs.append((district, left_url, right_url, similarity))
    return similar_pairs


def write_page(path: Path, content: str) -> None:
    require_owned_or_missing(path)
    if path.exists() and path.read_text(encoding="utf-8") == content:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excel", type=Path, required=True, help="Source XLSX file")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", metavar="AREA", help="Write a single noindex preview page")
    mode.add_argument("--all", action="store_true", help="Prepare all workbook pages and district lists")
    parser.add_argument("--district", help="District name required with --sample")
    parser.add_argument("--write", action="store_true", help="Write output; without this flag only validate")
    args = parser.parse_args()

    if args.sample and not args.district:
        parser.error("--district is required with --sample")
    if not args.excel.is_file():
        parser.error(f"Excel workbook not found: {args.excel}")

    try:
        rows = read_workbook(args.excel)
        assign_district_order(rows)
        copy_data = load_copy_data()
        directories = district_directory_map()
        if args.sample:
            row = next(
                (
                    item
                    for item in rows
                    if item["area"].casefold() == args.sample.casefold()
                    and item["district"].casefold() == args.district.casefold()
                ),
                None,
            )
            if row is None:
                raise ValueError(f"Area not found in workbook: {args.sample}, {args.district}")
            row["sr_no"] = "1"
            page, url_path, main_text = render_page(row, rows, copy_data, sample=True)
            validate_page_links(page, {url_path}, page_name=url_path)
            output = district_directory(row["district"], directories) / area_slug(row) / "index.html"
            if args.write:
                write_page(output, page)
                print(f"Wrote noindex sample page: {output}")
            else:
                print(f"Validated sample preview only: {url_path}")
            print(
                "Sample visible main-content word count "
                f"(not unique-copy qualification): {len(main_text.split())}"
            )
            return 0

        pages = []
        for index, row in enumerate(rows, start=1):
            row["sr_no"] = str(index)
            page, url_path, main_text = render_page(row, rows, copy_data, sample=False)
            pages.append((row, page, url_path, main_text))
        similar_pairs = validate_bulk_pages(pages)
        if similar_pairs:
            highest_similarity = max(similar_pairs, key=lambda item: item[3])
            print(
                f"Similarity notice: {len(similar_pairs)} same-district page pairs "
                "exceed 60%; highest is "
                f"{highest_similarity[3]:.0%} in {highest_similarity[0]} "
                f"({highest_similarity[1]} and {highest_similarity[2]})."
            )
        grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in rows:
            grouped[row["district"]].append(row)
        for district, area_rows in grouped.items():
            directory = district_directory(district, directories)
            district_page = directory / "index.html"
            existing = district_page.read_text(encoding="utf-8")
            find_district_area_grid(existing, district_page)
        if args.write:
            generated_paths = {url_path for _, _, url_path, _ in pages}
            changed_paths: set[str] = set()
            for row, page, url_path, _ in pages:
                validate_page_links(page, generated_paths, page_name=url_path)
                output = district_directory(row["district"], directories) / area_slug(row) / "index.html"
                require_owned_or_missing(output)
                if not output.exists() or output.read_text(encoding="utf-8") != page:
                    write_page(output, page)
                    changed_paths.add(url_path)
            legacy_notes: dict[str, list[str]] = {}
            for district, area_rows in grouped.items():
                district_file = district_directory(district, directories) / "index.html"
                old_page = district_file.read_text(encoding="utf-8")
                legacy_notes[district] = update_district_page(
                    district_file,
                    district,
                    area_rows,
                    directories,
                )
                if district_file.read_text(encoding="utf-8") != old_page:
                    changed_paths.add(f"/{district_directory(district, directories).name}/")
                district_content = district_file.read_text(encoding="utf-8")
                expected_area_urls = [area_url(row, directories) for row in area_rows]
                found_links = re.findall(
                    r"""<a\b[^>]*href=["']([^"']+)["']""",
                    district_content,
                    re.I,
                )
                if any(found_links.count(url) != 1 for url in expected_area_urls):
                    raise ValueError(
                        f"Expected each of {len(area_rows)} area URLs exactly once on "
                        f"{district_file}"
                    )
                if len(expected_area_urls) != sum(url in found_links for url in expected_area_urls):
                    raise ValueError(f"District link count mismatch on {district_file}")
                if not re.search(
                    r"(?is)\.district-area-link:hover.*?\.district-area-link:focus-visible",
                    district_content,
                ):
                    raise ValueError(f"Missing hover/focus styles on {district_file}")
                print(f"{district}: Excel={len(area_rows)} links={len(expected_area_urls)} match=yes")
            sitemap_root = ET.parse(SITEMAP_FILE).getroot()
            sitemap_locations = {
                item.findtext(f"{{{SITEMAP_NS}}}loc")
                for item in sitemap_root.findall(f"{{{SITEMAP_NS}}}url")
            }
            expected_sitemap_urls = {
                f"{BASE_URL}{url_path}" for _, _, url_path, _ in pages
            }
            expected_sitemap_urls.update(
                f"{BASE_URL}/{district_directory(district, directories).name}/"
                for district in grouped
            )
            missing_sitemap_urls = sorted(expected_sitemap_urls - sitemap_locations)
            if missing_sitemap_urls:
                update_sitemap(
                    [url_path for _, _, url_path, _ in pages],
                    sorted(grouped),
                    directories,
                    changed_paths,
                )
                print(f"Added {len(missing_sitemap_urls)} missing URL(s) to sitemap.xml.")
            else:
                print("Sitemap unchanged: every district and area URL was already present.")
            for district, names in legacy_notes.items():
                if names:
                    print(f"Retained unlinked legacy names in {district}: {', '.join(names)}")
            print(
                f"Wrote/updated {len(pages)} area pages and {len(grouped)} district pages; "
                "district links validated."
            )
        else:
            print(f"Validated {len(pages)} candidate pages; no files written.")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        print(f"Generation stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
