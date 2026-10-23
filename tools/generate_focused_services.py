#!/usr/bin/env python3
"""Generate the approved pest-specific and construction-stage service pages."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_footer import apply_main_footer
from tools.page_images import image_for_topic
from tools.site_schema import website_schema

DATA = ROOT / "data" / "focused-services.json"
SITEMAP = ROOT / "sitemap.xml"
BASE_URL = "https://www.superpest.in"
SITEMAP_BASE_URL = "https://www.superpest.in"
BUSINESS_ID = "https://www.superpest.in/#business"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
DISTRICT_LINKS_ENABLED = True
GENERATED_MARKER = "<!-- GENERATED FOCUSED SERVICE LINKS -->"
DISTRICT_START = "<!-- BEGIN GENERATED FOCUSED DISTRICT SERVICES -->"
DISTRICT_END = "<!-- END GENERATED FOCUSED DISTRICT SERVICES -->"
CUSTOMER_START = "<!-- BEGIN GENERATED FOCUSED CUSTOMER SERVICES -->"
CUSTOMER_END = "<!-- END GENERATED FOCUSED CUSTOMER SERVICES -->"

RELATED_SERVICES = {
    "ant-control": [
        ("General Pest Control for common crawling pests", "/services/general-pest-control/"),
        ("Cockroach Control services", "/services/cockroach-control/"),
        ("Commercial AMC (IPM) services", "/services/commercial-amc-ipm/"),
    ],
    "pre-construction-anti-termite-treatment": [
        ("Termite Control for existing buildings", "/services/termite-control/"),
        ("Termite Piping System for construction-stage recharge access", "/services/termite-piping-system/"),
        ("Wood Borer Control services", "/services/wood-borer-control/"),
    ],
    "termite-piping-system": [
        ("Pre-Construction Anti-Termite Treatment", "/services/pre-construction-anti-termite-treatment/"),
        ("Termite Control for existing buildings", "/services/termite-control/"),
        ("Wood Borer Control services", "/services/wood-borer-control/"),
    ],
}
NEW_SERVICE_LINKS = [
    ("Ant Control", "/services/ant-control/"),
    ("Pre-Construction Anti-Termite Treatment", "/services/pre-construction-anti-termite-treatment/"),
    ("Termite Piping System", "/services/termite-piping-system/"),
    ("Wasp & Hornet Nest Removal", "/services/wasp-hornet-nest-removal/"),
]
CUSTOMER_SERVICE_LABELS = {
    "ant-control": "Ant Control assessment for kitchens and occupied premises",
    "pre-construction-anti-termite-treatment": "Pre-Construction Anti-Termite Treatment for new builds and project sites",
    "termite-piping-system": "Termite Piping System planning for future recharge access",
}


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def strip_markup(text: str) -> str:
    text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def visible_main_word_count(page_html: str) -> int:
    main = page_html.split("<main", 1)[1].split("</main>", 1)[0]
    return word_count(strip_markup(main))


def page_url(page: dict[str, Any]) -> str:
    return f"/services/{page['slug']}/"


def render_schema(page: dict[str, Any], url: str) -> str:
    faq = [
        {
            "@type": "Question",
            "name": question,
            "acceptedAnswer": {"@type": "Answer", "text": answer},
        }
        for question, answer in page["faqs"]
    ]
    graph = [
        website_schema(),
        {
            "@type": "WebPage",
            "@id": f"{url}#webpage",
            "url": url,
            "name": page["title"],
            "description": page["description"],
            "isPartOf": {"@id": f"{BASE_URL}/#website"},
            "about": {"@id": f"{url}#service"},
            "publisher": {"@id": BUSINESS_ID},
        },
        {
            "@type": "Service",
            "@id": f"{url}#service",
            "name": page["name"],
            "serviceType": page["name"],
            "provider": {"@id": BUSINESS_ID},
            "areaServed": {"@type": "State", "name": "Rajasthan"},
            "url": url,
        },
        {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Services", "item": f"{BASE_URL}/services/"},
                {"@type": "ListItem", "position": 3, "name": page["name"], "item": url},
            ],
        },
        {"@type": "FAQPage", "mainEntity": faq},
    ]
    return (
        '<script type="application/ld+json">\n'
        + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, indent=2)
        + "\n</script>"
    )


def image_html(filename: str, alt: str) -> str:
    return (
        f'<figure class="focused-image"><img src="/images/{esc(filename)}" '
        f'alt="{esc(alt)}" '
        f'width="1200" height="675" loading="lazy">'
        f'<figcaption>{esc(alt)}</figcaption></figure>'
    )


def table_html(comparison: dict[str, Any] | None) -> str:
    if comparison is None:
        return ""
    headers = "".join(f"<th scope=\"col\">{esc(item)}</th>" for item in comparison["headers"])
    rows = "".join(
        "<tr>" + "".join(f"<td>{esc(cell)}</td>" for cell in row) + "</tr>"
        for row in comparison["rows"]
    )
    return (
        '<div class="focused-table-wrap"><table><caption>'
        + esc(comparison["caption"])
        + f"</caption><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>"
    )


def render_faqs(page: dict[str, Any]) -> str:
    result = []
    for index, (question, answer) in enumerate(page["faqs"]):
        language = ' lang="hi"' if index >= len(page["faqs"]) - 2 else ""
        result.append(
            f"<details{language}><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>"
        )
    return "\n".join(result)


def toc_html(page: dict[str, Any]) -> str:
    targets = [(item["id"], item["heading"]) for item in page["sections"]]
    targets += [
        ("process", "How the service is planned"),
        ("related-services", "Related services"),
        ("who-we-serve", "Who we serve"),
        ("areas-we-serve", "Areas we serve"),
        ("faqs", "Frequently asked questions"),
    ]
    if page.get("comparison"):
        targets.append(("comparison", page["comparison"]["caption"]))
    targets.append(("hindi-summary", page["hindi"]["heading"]))
    return "\n".join(
        f'<li><a href="#{esc(target)}">{esc(label)}</a></li>' for target, label in targets
    )


def render_page(page: dict[str, Any]) -> str:
    route = page_url(page)
    url = BASE_URL + route
    toc = toc_html(page)
    section_blocks = []
    image_filename, image_alt = image_for_topic(page["id"])
    image_positions = {1: 0}
    for index, section in enumerate(page["sections"]):
        paragraphs = "".join(f"<p>{esc(text)}</p>" for text in section["paragraphs"])
        content = f'<section id="{esc(section["id"])}"><h2>{esc(section["heading"])}</h2>{paragraphs}'
        if section["id"] == "comparison-of-termite-options":
            content += f'<div id="comparison"><h3>{esc(page["comparison"]["caption"])}</h3>{table_html(page["comparison"])}</div>'
        content += "</section>"
        section_blocks.append(content)
        if index in image_positions:
            section_blocks.append(image_html(image_filename, image_alt))

    step_html = "".join(
        f'<li><span>{index:02d}</span><div><h3>{esc(title)}</h3><p>{esc(text)}</p></div></li>'
        for index, (title, text) in enumerate(page["steps"], start=1)
    )
    related = "".join(
        f'<li><a href="{esc(href)}">{esc(label)}</a></li>'
        for label, href in RELATED_SERVICES[page["id"]]
    )
    customer_links = "".join(
        f'<li><a href="{esc(href)}">{esc(label)}</a></li>'
        for href, label in page["customer_links"]
    )
    faq_html = render_faqs(page)
    hindi = "".join(f"<p>{esc(item)}</p>" for item in page["hindi"]["paragraphs"])
    schema = render_schema(page, url)
    title = esc(page["title"])
    description = esc(page["description"],)
    intro = esc(page["hero"])
    updated = date.today().isoformat()

    page_html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{description}">
    <meta name="robots" content="index, follow">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:url" content="{url}">
    <meta property="og:image" content="{BASE_URL}/images/{image_filename}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{BASE_URL}/images/{image_filename}">
    {schema}
    <link rel="icon" type="image/webp" href="/images/Logooo.webp">
    <link rel="preload" href="/css/style.min.css" as="style" fetchpriority="high" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="/css/style.min.css"></noscript>
    <style>
        .focused-main{{width:min(1060px,92%);margin:0 auto;padding:118px 0 72px;color:#334239;line-height:1.75}}
        .focused-main h1,.focused-main h2,.focused-main h3{{color:#173e2e}}
        .focused-main h1{{font-family:Georgia,"Times New Roman",serif;font-size:clamp(32px,5vw,48px);line-height:1.15}}
        .focused-main h2{{margin:34px 0 10px;font-size:clamp(23px,3vw,31px)}}
        .focused-main h3{{margin:18px 0 8px;font-size:19px}}
        .focused-main a{{color:#245c3d;text-underline-offset:3px}}
        .focused-breadcrumb,.focused-toc ul,.focused-links,.focused-steps{{padding:0;list-style:none}}
        .focused-breadcrumb{{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 18px;font-size:14px}}
        .focused-hero{{padding:34px 0 26px}}
        .focused-actions,.focused-links{{display:flex;flex-wrap:wrap;gap:12px;margin:18px 0}}
        .focused-actions a,.focused-links a{{display:inline-flex;padding:11px 16px;border:1px solid #dce5df;border-radius:8px;font-weight:700;text-decoration:none}}
        .focused-actions a:first-child{{background:#5d951b;color:#fff}}
        .focused-toc,.focused-note{{padding:20px 24px;border:1px solid #e3ebe6;border-radius:12px;background:#f5f7f2}}
        .focused-toc ul{{columns:2;column-gap:30px;margin:8px 0 0}}
        .focused-toc li{{break-inside:avoid;margin:4px 0}}
        .focused-image{{margin:24px 0;overflow:hidden;border-radius:14px;background:#eef2eb}}
        .focused-image img{{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}}
        .focused-image figcaption{{padding:8px 12px;color:#526157;font-size:13px}}
        .focused-steps{{display:grid;gap:12px;counter-reset:step}}
        .focused-steps li{{display:grid;grid-template-columns:44px 1fr;gap:14px;padding:16px;border:1px solid #e3ebe6;border-radius:12px;background:#fff}}
        .focused-steps li>span{{display:grid;place-items:center;width:38px;height:38px;border-radius:50%;background:#173e2e;color:#fff;font-weight:700}}
        .focused-steps h3,.focused-steps p{{margin:0}}
        .focused-table-wrap{{overflow-x:auto}}
        .focused-main table{{width:100%;border-collapse:collapse;min-width:640px;background:#fff}}
        .focused-main th,.focused-main td{{padding:12px;border:1px solid #dce5df;text-align:left;vertical-align:top}}
        .focused-main th{{background:#eef2eb;color:#173e2e}}
        .focused-main caption{{padding:10px;font-weight:700;text-align:left}}
        .focused-faq details{{margin:10px 0;padding:16px 20px;border:1px solid #e3ebe6;border-radius:10px;background:#fff}}
        .focused-faq summary{{color:#173e2e;font-weight:700;cursor:pointer}}
        .focused-faq p{{margin:10px 0 0}}
        .focused-hi{{padding:18px 22px;border-left:4px solid #79b82a;background:#f1f6ed}}
        .focused-cta{{margin-top:34px;padding:26px;border-radius:14px;background:#173e2e;color:#fff}}
        .focused-cta h2,.focused-cta p{{color:#fff}}
        .focused-cta a{{display:inline-flex;margin:5px 10px 0 0;padding:10px 16px;border-radius:24px;background:#79b82a;color:#101610;font-weight:700;text-decoration:none}}
        .focused-updated{{margin-top:26px;color:#526157;font-size:14px}}
        @media(max-width:700px){{.focused-main{{padding-top:96px}}.focused-toc ul{{columns:1}}.focused-steps li{{grid-template-columns:36px 1fr;gap:10px;padding:12px}}.focused-steps li>span{{width:32px;height:32px}}.focused-actions a{{flex:1 1 100%;justify-content:center}}}}
    </style>
</head>
<body>
<header class="header"><nav class="navbar" aria-label="Main navigation">
    <a href="/" class="logo"><div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" loading="eager" alt="Super Pest Control Services"></div><div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div></a>
    <div class="nav-links"><a href="/">Home</a><a href="/services/" class="active">Services</a><a href="/residential-pest-control/">Residential</a><a href="/commercial-pest-control/">Commercial</a><a href="/about/">About</a><a href="/blog/">Blogs</a><a href="/service-location/">Service Location</a><a href="/contact/">Contact</a></div>
    <a href="/contact/" class="nav-btn">Book Service</a>
    <button class="menu-btn" id="menuBtn" type="button" aria-label="Open navigation menu">☰</button>
</nav></header>
<main class="focused-main">
    <nav aria-label="Breadcrumb"><ol class="focused-breadcrumb"><li><a href="/">Home</a></li><li><a href="/services/">Services</a></li><li aria-current="page">{esc(page["name"])}</li></ol></nav>
    <section class="focused-hero"><span>PEST MANAGEMENT • RAJASTHAN</span><h1>{esc(page["name"])}</h1><p>{intro}</p><div class="focused-actions"><a href="tel:+919828066990">Call +91 98280 66990 for {esc(page["name"])}</a><a href="https://wa.me/917976572984?text=Hello%2C%20I%20would%20like%20to%20discuss%20{page["slug"].replace("-", "%20")}%20in%20Rajasthan." target="_blank" rel="noopener">WhatsApp the Super Pest service team about {esc(page["name"])}</a><a href="/contact/#booking">Request a property-specific {esc(page["name"])} assessment</a></div></section>
    <nav class="focused-toc" aria-label="Table of contents"><h2>On this page</h2><ul>{toc}</ul></nav>
    {"".join(section_blocks)}
    <section id="process"><h2>How the service is planned</h2><p>The steps below outline a service discussion. The actual sequence and treatment are confirmed for the inspected property and the approved scope.</p><ol class="focused-steps">{step_html}</ol></section>
    {f'<section id="comparison"><h2>{esc(page["comparison"]["caption"])}</h2>{table_html(page["comparison"])}</section>' if page.get("comparison") and "comparison-of-termite-options" not in [item["id"] for item in page["sections"]] else ""}
    <section id="related-services"><h2>Related services</h2><p>These services address different pest situations or construction stages. Choose the page that matches your property and timing.</p><ul class="focused-links">{related}</ul></section>
    <section id="who-we-serve"><h2>Who we serve</h2><p>We discuss service scope with owners, residents, builders and commercial site contacts according to the pest concern and property access.</p><ul class="focused-links">{customer_links}</ul></section>
    <section id="areas-we-serve"><h2>Areas we serve</h2><p>Super Pest Control Services serves customers across Rajasthan. View the <a href="/service-location/">Rajasthan pest control service locations</a> and district pages for local coverage, or ask us to confirm availability for your property.</p><ul class="focused-links"><li><a href="/pest-control-in-jaipur/">Pest control services in Jaipur</a></li><li><a href="/pest-control-in-ajmer/">Pest control services in Ajmer</a></li><li><a href="/pest-control-in-jodhpur/">Pest control services in Jodhpur</a></li><li><a href="/pest-control-in-kota/">Pest control services in Kota</a></li><li><a href="/pest-control-in-udaipur/">Pest control services in Udaipur</a></li><li><a href="/service-location/">Browse pest control service locations across Rajasthan</a></li></ul></section>
    <section id="hindi-summary" class="focused-hi" lang="hi"><h2>{esc(page["hindi"]["heading"])}</h2>{hindi}</section>
    <section id="faqs"><h2>Frequently asked questions about {esc(page["name"])}</h2><div class="focused-faq">{faq_html}</div></section>
    <section class="focused-cta"><h2>Request a property-specific discussion</h2><p>Tell us the property type, location, visible signs or construction stage. The team can discuss inspection, scope, access and a quotation.</p><a href="tel:+919828066990">Call +91 98280 66990</a><a href="tel:+917976572984">Call +91 79765 72984</a><a href="https://wa.me/917976572984" target="_blank" rel="noopener">WhatsApp Super Pest Control Services</a><a href="/contact/#booking">Request a service assessment</a></section>
    <p class="focused-updated">Last updated: {updated}</p>
</main>
<footer class="footer"><div class="footer-grid">
    <div class="footer-brand"><a href="/" class="logo"><div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" loading="lazy" alt="Super Pest Control Services"></div><div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div></a><p>Super Pest Control Services provides pest-management services for residential and commercial properties. Treatment recommendations and precautions depend on the pest and premises.</p></div>
    <div class="footer-column"><h3>Quick Links</h3><a href="/">Home</a><a href="/services/">Pest control services</a><a href="/commercial-pest-control/">Commercial pest control and customer types</a><a href="/about/">About Super Pest Control Services</a><a href="/blog/">Pest management articles</a><a href="/service-location/">Pest control service locations</a><a href="/contact/">Contact Super Pest Control Services</a><!-- BEGIN GENERATED LEGAL FOOTER LINKS --><a href="/privacy-policy/">Privacy Policy</a><a href="/terms-and-conditions/">Terms &amp; Conditions</a><!-- END GENERATED LEGAL FOOTER LINKS --></div>
    <div class="footer-column"><h3>Services</h3><a href="/services/termite-control/">Termite Control</a><a href="/services/general-pest-control/">General Pest Control</a><a href="/services/ant-control/">Ant Control</a><a href="/services/pre-construction-anti-termite-treatment/">Pre-Construction Anti-Termite Treatment</a><a href="/services/termite-piping-system/">Termite Piping System</a><a href="/services/wood-borer-control/">Wood Borer Control</a><a href="/services/wasp-hornet-nest-removal/">Wasp &amp; Hornet Nest Removal</a><a href="/contact/">Any Other Pests?</a></div>
    <div class="footer-column"><h3>Contact</h3><a href="tel:+919828066990">Call +91 98280 66990</a><a href="tel:+917976572984">Call +91 79765 72984</a><a href="mailto:superpestcontrolservices.jaipur@gmail.com">Email Super Pest Control Services</a><p>Jaipur, Rajasthan</p></div>
</div><div class="footer-bottom"><p>© 2026 Super Pest Control Services. All Rights Reserved.</p></div></footer>
<script src="/js/script.min.js?v=20260906" defer></script>
</body>
</html>
"""
    return apply_main_footer(page_html)


def district_section() -> str:
    cards = "".join(
        '<li style="flex:0 1 320px;border:1px solid #e3ebe6;border-radius:10px;background:#fff;">'
        f'<a style="display:block;padding:14px 18px;color:#173e2e;font-family:Georgia,'
        f"'Times New Roman',serif;font-size:18px;line-height:1.45;font-weight:700;"
        f'text-decoration:none;" href="{href}">{esc(label)}</a></li>'
        for label, href in NEW_SERVICE_LINKS
    )
    return (
        f'{DISTRICT_START}<section class="campaign-district-services" '
        f'aria-label="Related services" style="max-width:1060px;width:92%;margin:48px auto;'
        f'padding:24px 0;text-align:center;"><h2>Related services</h2>'
        f'<ul class="campaign-cards" style="display:flex;flex-wrap:wrap;justify-content:center;'
        f'gap:14px;padding:0;list-style:none;">{cards}</ul></section>{DISTRICT_END}'
    )


def update_page_section(path: Path, section: str) -> bool:
    content = path.read_text(encoding="utf-8")
    if DISTRICT_START in content and DISTRICT_END in content:
        updated = re.sub(
            re.escape(DISTRICT_START) + r".*?" + re.escape(DISTRICT_END),
            section,
            content,
            flags=re.S,
        )
    else:
        match = re.search(r"</main>", content, re.I)
        if match is None:
            raise ValueError(f"Could not locate main closing tag: {path}")
        updated = content[: match.start()] + section + content[match.start() :]
    if updated != content:
        path.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def add_footer_links(path: Path) -> bool:
    content = path.read_text(encoding="utf-8")
    footer_match = re.search(r"<footer\b.*?</footer>", content, re.I | re.S)
    if footer_match is None:
        raise ValueError(f"Missing footer in {path}")
    footer = footer_match.group()
    services_column = re.search(
        r'(<div\b[^>]*class="footer-column"[^>]*>\s*<h3>\s*(?:Services|Related services)\s*</h3>.*?)(</div>)',
        footer,
        re.I | re.S,
    )
    if services_column is None:
        return False
    inside = services_column.group(1)
    before = inside
    existing_hrefs = set(re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\']', inside, re.I))
    insert = "".join(
        f'<a href="{href}">{esc(label)}</a>'
        for label, href in NEW_SERVICE_LINKS
        if href not in existing_hrefs
    )
    inside += insert
    any_other_pattern = re.compile(
        r'<a\b[^>]*href=["\']/contact/["\'][^>]*>\s*Any Other Pests\?\s*</a>',
        re.I,
    )
    inside = any_other_pattern.sub("", inside)
    wasp_link = re.search(
        r'<a\b[^>]*href=["\']/services/wasp-hornet-nest-removal/["\'][^>]*>.*?</a>',
        inside,
        re.I | re.S,
    )
    if wasp_link is None:
        raise ValueError(f"Missing wasp service link in footer for {path}")
    inside = (
        inside[: wasp_link.end()]
        + '<a href="/contact/">Any Other Pests?</a>'
        + inside[wasp_link.end() :]
    )
    if inside == before:
        return False
    footer = footer[: services_column.start(1)] + inside + footer[services_column.end(1) :]
    updated = content[: footer_match.start()] + footer + content[footer_match.end() :]
    if updated != content:
        path.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def add_related_service_block(path: Path, links: list[tuple[str, str]]) -> bool:
    content = path.read_text(encoding="utf-8")
    marker_start = f"{GENERATED_MARKER} BEGIN"
    marker_end = f"{GENERATED_MARKER} END"
    link_html = "".join(f'<li><a href="{href}">{esc(label)}</a></li>' for label, href in links)
    block = (
        f"{marker_start}<section class=\"section content-section\"><div>"
        f"<h2>Related focused pest-management services</h2>"
        f"<p>These pages explain separate treatment situations and construction stages.</p>"
        f'<ul class="termite-related-links">{link_html}</ul></div></section>{marker_end}'
    )
    if marker_start in content and marker_end in content:
        updated = re.sub(re.escape(marker_start) + r".*?" + re.escape(marker_end), block, content, flags=re.S)
    else:
        match = re.search(r"</main>", content, re.I)
        if match is None:
            raise ValueError(f"Could not locate main closing tag in {path}")
        updated = content[:match.start()] + block + content[match.start():]
    if updated != content:
        path.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def update_customer_service_block(path: Path, service_ids: list[str]) -> bool:
    content = path.read_text(encoding="utf-8")
    related_section = re.search(
        r'(<section\b[^>]*>\s*<h2>\s*Related pest-management services\s*</h2>.*?<ul\b[^>]*>)(.*?)(</ul>.*?</section>)',
        content,
        re.I | re.S,
    )
    if related_section is None:
        raise ValueError(f"Could not locate related-services list in {path}")
    list_content = related_section.group(2)
    if CUSTOMER_START in list_content and CUSTOMER_END in list_content:
        list_content = re.sub(
            re.escape(CUSTOMER_START) + r".*?" + re.escape(CUSTOMER_END),
            "",
            list_content,
            flags=re.S,
        )
    existing_hrefs = set(re.findall(r'<a\b[^>]*href="(/services/[^"]+)"', list_content))
    links = "".join(
        f'<li><a href="/services/{service_id}/">{esc(CUSTOMER_SERVICE_LABELS[service_id])}</a></li>'
        for service_id in service_ids
        if f"/services/{service_id}/" not in existing_hrefs
    )
    marker_block = f"{CUSTOMER_START}{links}{CUSTOMER_END}" if links else ""
    updated_list = list_content + marker_block
    updated = (
        content[:related_section.start(2)]
        + updated_list
        + content[related_section.end(2):]
    )
    if updated != content:
        path.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def add_services_index_cards() -> bool:
    path = ROOT / "services" / "index.html"
    content = path.read_text(encoding="utf-8")
    start = "<!-- BEGIN GENERATED FOCUSED SERVICE CARDS -->"
    end = "<!-- END GENERATED FOCUSED SERVICE CARDS -->"
    cards = [
        ("🐜", "Ant Control", "Inspection-led ant management for kitchens, homes and business premises.", "/services/ant-control/"),
        ("🏗️", "Pre-Construction Anti-Termite Treatment", "Coordinate foundation and soil treatment while construction interfaces are accessible.", "/services/pre-construction-anti-termite-treatment/"),
        ("🛠️", "Termite Piping System", "Plan future recharge access through a construction-stage pipe network.", "/services/termite-piping-system/"),
        ("🐝", "Wasp & Hornet Nest Removal", "Professional inspection and safe removal planning for stinging-insect nests.", "/services/wasp-hornet-nest-removal/"),
    ]
    card_html = "".join(
        f'<article class="service-card"><div class="service-icon">{icon}</div>'
        f'<h3><a href="{href}">{esc(title)}</a></h3><p>{esc(description)}</p>'
        f'<a href="{href}">Explore {esc(title.lower())} services →</a>'
        '<a href="/contact/">Request a service assessment →</a></article>'
        for icon, title, description, href in cards
    )
    block = f"{start}{card_html}{end}"
    if start in content and end in content:
        updated = re.sub(re.escape(start) + r".*?" + re.escape(end), block, content, flags=re.S)
    else:
        target = re.search(r'<article class="service-card">\s*<div class="service-icon">🐞</div>', content)
        if target is None:
            raise ValueError("Could not locate the final service card insertion point")
        updated = content[:target.start()] + block + content[target.start():]
    if updated != content:
        path.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def update_sitemap(pages: list[dict[str, Any]]) -> int:
    ET.register_namespace("", SITEMAP_NS)
    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    existing = {
        node.findtext(f"{{{SITEMAP_NS}}}loc"): node
        for node in root.findall(f"{{{SITEMAP_NS}}}url")
    }
    added = 0
    for page in pages:
        url = SITEMAP_BASE_URL + page_url(page)
        node = existing.get(url)
        if node is None:
            node = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
            ET.SubElement(node, f"{{{SITEMAP_NS}}}loc").text = url
            ET.SubElement(node, f"{{{SITEMAP_NS}}}lastmod").text = date.today().isoformat()
            ET.SubElement(node, f"{{{SITEMAP_NS}}}priority").text = "0.8"
            added += 1
        else:
            lastmod = node.find(f"{{{SITEMAP_NS}}}lastmod")
            if lastmod is None:
                lastmod = ET.SubElement(node, f"{{{SITEMAP_NS}}}lastmod")
            lastmod.text = date.today().isoformat()
    tree.write(SITEMAP, encoding="UTF-8", xml_declaration=True)
    return added


def validate(pages: list[dict[str, Any]], rendered: dict[str, str]) -> None:
    if len(pages) != 3 or len({p["slug"] for p in pages}) != 3:
        raise ValueError("Expected exactly three unique focused service pages")
    texts: list[tuple[str, str]] = []
    for page in pages:
        route = page_url(page)
        title = page["title"]
        if page["primary_keyword"].casefold() not in title.casefold():
            raise ValueError(f"{page['id']}: primary keyword missing from title")
        page_html = rendered[page["id"]]
        if "[[TO-FILL:" in page_html:
            raise ValueError(f"{page['id']}: unresolved placeholder marker in rendered content")
        main = page_html.split("<main", 1)[1].split("</main>", 1)[0]
        body = strip_markup(main)
        if word_count(body) < 1800 or word_count(body) > 2500:
            raise ValueError(
                f"{page['id']}: visible word count {word_count(body)} is outside 1,800-2,500"
            )
        if word_count(body[:500]) < 1:
            raise ValueError(f"{page['id']}: empty page body")
        first_words = " ".join(body.split()[:100]).casefold()
        if page["primary_keyword"].casefold() not in first_words:
            raise ValueError(f"{page['id']}: primary keyword missing from first 100 visible words")
        if route.strip("/").split("/")[-1] not in page_html:
            raise ValueError(f"{page['id']}: route slug missing")
        if len(re.findall(r"<h1(?:\s|>)", page_html, re.I)) != 1:
            raise ValueError(f"{page['id']}: expected exactly one H1")
        if len(page["faqs"]) < 8 or len(page["faqs"]) > 10:
            raise ValueError(f"{page['id']}: expected 8-10 FAQs")
        links = re.findall(r'<a\b[^>]*href="(/[^"]+)"', page_html)
        if len(links) < 4:
            raise ValueError(f"{page['id']}: fewer than four internal links")
        texts.append((page["id"], body))
    for index, (name_a, text_a) in enumerate(texts):
        for name_b, text_b in texts[index + 1 :]:
            similarity = difflib.SequenceMatcher(None, text_a.casefold(), text_b.casefold()).ratio()
            if similarity > 0.40:
                raise ValueError(f"New-page similarity exceeds 40%: {name_a}/{name_b}={similarity:.1%}")


def run(write: bool) -> int:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    pages = data.get("services", [])
    rendered = {page["id"]: render_page(page) for page in pages}
    validate(pages, rendered)

    if not write:
        print("Audit summary: existing Termite Control and General Pest Control pages mention related topics; no dedicated pages exist.")
        for page in pages:
            print(f"Validated preview {page_url(page)} ({visible_main_word_count(rendered[page['id']])} visible words)")
        print("No files written.")
        return 0

    created = 0
    for page in pages:
        target = ROOT / "services" / page["slug"] / "index.html"
        desired = rendered[page["id"]]
        if not target.exists() or target.read_text(encoding="utf-8") != desired:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(desired, encoding="utf-8", newline="\n")
            created += 1

    related_changes = 0
    related_changes += add_related_service_block(
        ROOT / "services" / "termite-control" / "index.html",
        [
            ("Pre-Construction Anti-Termite Treatment for new buildings", "/services/pre-construction-anti-termite-treatment/"),
            ("Termite Piping System for planned recharge access", "/services/termite-piping-system/"),
        ],
    )
    related_changes += add_related_service_block(
        ROOT / "services" / "general-pest-control" / "index.html",
        [
            ("Ant Control for kitchen and property ant activity", "/services/ant-control/"),
            ("Wasp and hornet nest removal for stinging-insect nests", "/services/wasp-hornet-nest-removal/"),
        ],
    )
    for service_slug in (
        "fly-management-systems",
        "bed-bug-eradication",
        "commercial-amc-ipm",
    ):
        related_changes += add_related_service_block(
            ROOT / "services" / service_slug / "index.html",
            [("Wasp and hornet nest removal for stinging-insect nests", "/services/wasp-hornet-nest-removal/")],
        )

    service_index_changed = add_services_index_cards()
    footer_changes = 0
    for path in ROOT.rglob("*.html"):
        if path.parent.name in {page["slug"] for page in pages} | {"wasp-hornet-nest-removal"}:
            continue
        footer_changes += add_footer_links(path)

    district_changes = 0
    if DISTRICT_LINKS_ENABLED:
        district_section_html = district_section()
        for path in ROOT.glob("pest-control-in-*/index.html"):
            district_changes += update_page_section(path, district_section_html)

    customer_data = json.loads((ROOT / "data" / "customer-pages.json").read_text(encoding="utf-8"))
    customer_by_id = {item["id"]: item for item in customer_data["customer_types"]}
    customer_changes = 0
    for customer_id, customer in customer_by_id.items():
        service_ids = customer.get("focused_services", [])
        if not service_ids:
            continue
        invalid_services = set(service_ids) - set(CUSTOMER_SERVICE_LABELS)
        if invalid_services:
            raise ValueError(f"Unknown focused services for {customer_id}: {sorted(invalid_services)}")
        customer_page = ROOT / customer["slug"] / "index.html"
        if not customer_page.is_file():
            raise ValueError(f"Missing customer page for focused services: {customer_page}")
        customer_changes += update_customer_service_block(customer_page, service_ids)

    service_area_generator = ROOT / "tools" / "generate_service_areas.py"
    area_source = service_area_generator.read_text(encoding="utf-8")
    if 'href="/services/ant-control/"' not in area_source:
        area_source = area_source.replace(
            '                <a href="/services/termite-control/">Termite Treatment</a>',
            '                <a href="/services/ant-control/">Ant Control</a>\n'
            '                <a href="/services/pre-construction-anti-termite-treatment/">Pre-Construction Anti-Termite Treatment</a>\n'
            '                <a href="/services/termite-piping-system/">Termite Piping System</a>\n'
            '                <a href="/services/termite-control/">Termite Treatment</a>',
            1,
        )
        service_area_generator.write_text(area_source, encoding="utf-8", newline="\n")
    elif "/services/pre-construction-anti-termite-treatment/" not in area_source or "/services/termite-piping-system/" not in area_source:
        raise ValueError("Service-area generator contains a partial focused-service update")

    sitemap_added = update_sitemap(pages)
    print(f"Created/updated {created} focused service pages.")
    print(f"Updated existing related-service blocks: {related_changes}.")
    print(f"Updated Services index cards: {int(service_index_changed)}.")
    print(f"Updated footers with service links: {footer_changes} pages.")
    print(f"Added focused-service links to district pages: {district_changes}.")
    print(f"Updated customer-type focused-service blocks: {customer_changes}.")
    print(f"Added sitemap URLs: {sitemap_added}.")
    for page in pages:
        print(f"{page_url(page)} — {visible_main_word_count(rendered[page['id']])} visible words")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write generated pages and related internal links")
    args = parser.parse_args()
    try:
        return run(args.write)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as error:
        print(f"Focused service generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
