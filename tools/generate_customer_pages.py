#!/usr/bin/env python3
"""Generate the approved customer-type and verified city service pages."""

from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.generate_service_areas import (
    BASE_URL,
    area_url,
    district_directory,
    district_directory_map,
    district_path_slug,
    read_workbook,
    slugify,
)
from tools.site_footer import apply_main_footer
from tools.page_images import image_for_topic
from tools.site_claims import approved_claim


ROOT = PROJECT_ROOT
DATA_FILE = ROOT / "data" / "customer-pages.json"
SITEMAP_FILE = ROOT / "sitemap.xml"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
PAGE_MARKER = "<!-- GENERATED CUSTOMER PAGE:"
DISTRICT_START = "<!-- BEGIN GENERATED CUSTOMER SERVICE LINKS -->"
DISTRICT_END = "<!-- END GENERATED CUSTOMER SERVICE LINKS -->"
NAV_START = "<!-- BEGIN GENERATED INDUSTRIES NAV -->"
NAV_END = "<!-- END GENERATED INDUSTRIES NAV -->"
CUSTOMER_LINKS_START = "<!-- BEGIN GENERATED CUSTOMER TYPE LINKS -->"
CUSTOMER_LINKS_END = "<!-- END GENERATED CUSTOMER TYPE LINKS -->"
DISTRICT_DIRS = district_directory_map()

SERVICE_LABELS = {
    "ant-control": ("Ant Control", "/services/ant-control/"),
    "bed-bug-eradication": ("Bed Bug Eradication", "/services/bed-bug-eradication/"),
    "cockroach-control": ("Cockroach Control", "/services/cockroach-control/"),
    "commercial-amc-ipm": ("Commercial AMC (IPM)", "/services/commercial-amc-ipm/"),
    "commercial-fumigation": ("Commercial Fumigation", "/services/commercial-fumigation/"),
    "fly-management-systems": ("Fly Management Systems", "/services/fly-management-systems/"),
    "general-pest-control": ("General Pest Control", "/services/general-pest-control/"),
    "pre-construction-anti-termite-treatment": ("Pre-Construction Anti-Termite Treatment", "/services/pre-construction-anti-termite-treatment/"),
    "rodent-management": ("Rodent Management", "/services/rodent-management/"),
    "termite-control": ("Termite Control", "/services/termite-control/"),
    "termite-piping-system": ("Termite Piping System", "/services/termite-piping-system/"),
    "vector-control-fogging": ("Vector Control & Fogging", "/services/vector-control-fogging/"),
    "wood-borer-control": ("Wood Borer Control", "/services/wood-borer-control/"),
}

def esc(value: str) -> str:
    return html.escape(value, quote=True)


def words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)


def page_path(entry: dict[str, Any]) -> str:
    district = district_directory(entry["district"], DISTRICT_DIRS).name
    return f"/{district}/{slugify(entry['slug'])}/"


def area_row(
    entry: dict[str, Any], rows: list[dict[str, str]]
) -> dict[str, str] | None:
    if entry["area"].casefold() == entry["district"].casefold():
        return None
    found = [
        row
        for row in rows
        if row["district"].casefold() == entry["district"].casefold()
        and row["area"].casefold() == entry["area"].casefold()
    ]
    if len(found) != 1:
        raise ValueError(
            f"Expected one workbook row for {entry['area']}, {entry['district']}; "
            f"found {len(found)}"
        )
    return found[0]


def district_path(district: str) -> str:
    directory = district_directory(district, DISTRICT_DIRS).name
    return f"/{directory}/"


def customer_path(customer: dict[str, Any]) -> str:
    return f"/{slugify(customer['slug'])}/"


def anchor(label: str, href: str) -> str:
    return f'<a href="{esc(href)}">{esc(label)}</a>'


def service_links(service_ids: list[str]) -> str:
    missing = [key for key in service_ids if key not in SERVICE_LABELS]
    if missing:
        raise ValueError(f"Unknown service IDs: {', '.join(missing)}")
    return "\n".join(
        f'<li>{anchor(SERVICE_LABELS[key][0] + " in Rajasthan", SERVICE_LABELS[key][1])}</li>'
        for key in service_ids
    )


def replace_nav(content: str) -> str:
    content = re.sub(
        re.escape(NAV_START) + r".*?" + re.escape(NAV_END),
        "",
        content,
        flags=re.S,
    )
    return re.sub(
        r'<a\b[^>]*href="/industries/"[^>]*>.*?</a>',
        "",
        content,
        flags=re.I | re.S,
    )


def load_source() -> tuple[dict[str, Any], list[dict[str, str]]]:
    if not DATA_FILE.is_file():
        raise ValueError(f"Missing customer page data: {DATA_FILE}")
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    rows = read_workbook(ARGS.workbook)
    types = data.get("customer_types", [])
    city_pages = data.get("city_pages", [])
    if len(types) != 9:
        raise ValueError(f"Expected 9 customer types, found {len(types)}")
    if not city_pages:
        raise ValueError("No approved city pages are configured")
    type_ids = {item["id"] for item in types}
    if len(type_ids) != len(types):
        raise ValueError("Duplicate customer type IDs")
    for item in city_pages:
        if item["type"] not in type_ids:
            raise ValueError(f"Unknown customer type {item['type']} in {item['id']}")
        area_row(item, rows)
        directory = ROOT / f"pest-control-in-{district_path_slug(item['district'])}"
        if not (directory / "index.html").is_file():
            raise ValueError(f"Missing district page for {item['district']}")
        for service in item["services"]:
            if service not in SERVICE_LABELS:
                raise ValueError(f"Unapproved or missing service {service} in {item['id']}")
            if not (ROOT / SERVICE_LABELS[service][1].strip("/") / "index.html").is_file():
                raise ValueError(f"Service page does not exist: {service}")
        if item["id"] not in data.get("city_plans", {}):
            raise ValueError(f"Missing page-specific content plan for {item['id']}")
        item["plan"] = data["city_plans"][item["id"]]
    if set(data.get("city_plans", {})) != {item["id"] for item in city_pages}:
        raise ValueError("City content plans must match the approved city page IDs exactly")
    return data, rows


def schema_page(
    url: str,
    title: str,
    description: str,
    district: str,
    area: str,
    breadcrumbs: list[tuple[str, str]],
    faq_items: list[tuple[str, str]],
) -> str:
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "@id": f"{url}#service",
                "name": title,
                "serviceType": title.split(" in ")[0],
                "provider": {"@id": f"{BASE_URL}/#business"},
                "areaServed": [
                    {"@type": "Place", "name": area},
                    {"@type": "AdministrativeArea", "name": district},
                ],
                "url": url,
            },
            {
                "@type": "LocalBusiness",
                "@id": f"{BASE_URL}/#business",
                "name": "Super Pest Control Services",
                "url": f"{BASE_URL}/",
                "areaServed": [
                    {"@type": "Place", "name": area},
                    {"@type": "AdministrativeArea", "name": district},
                ],
            },
            {
                "@type": "WebPage",
                "@id": f"{url}#webpage",
                "url": url,
                "name": title,
                "description": description,
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "about": {"@id": f"{url}#service"},
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index,
                        "name": label,
                        "item": f"{BASE_URL}{path}",
                    }
                    for index, (label, path) in enumerate(breadcrumbs, start=1)
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": question,
                        "acceptedAnswer": {"@type": "Answer", "text": answer},
                    }
                    for question, answer in faq_items
                ],
            },
        ],
    }
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace(
        "</", "<\\/"
    )


def faq_html(items: list[tuple[str, str]]) -> str:
    return "\n".join(
        f"<details><summary>{esc(question)}</summary><p>{esc(answer)}</p></details>"
        for question, answer in items
    )


def page_head(
    url: str, title: str, description: str, schema: str, image_filename: str
) -> str:
    image = f"{BASE_URL}/images/{image_filename}"
    return f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{esc(title)}</title>
    <meta name="description" content="{esc(description)}">
    <link rel="canonical" href="{esc(url)}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{esc(title)}">
    <meta property="og:description" content="{esc(description)}">
    <meta property="og:url" content="{esc(url)}">
    <meta property="og:image" content="{image}">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{esc(title)}">
    <meta name="twitter:description" content="{esc(description)}">
    <meta name="twitter:image" content="{image}">
    <script type="application/ld+json">{schema}</script>
    <link rel="icon" type="image/webp" href="/images/Logooo.webp">
    <link rel="preload" href="/css/style.min.css" as="style" fetchpriority="high" onload="this.onload=null;this.rel='stylesheet'">
    <noscript><link rel="stylesheet" href="/css/style.min.css"></noscript>
</head>
<body>
<header class="header"><nav class="navbar" aria-label="Main navigation">
    <a href="/" class="logo"><div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" alt="Super Pest Control Services"></div><div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div></a>
    <div class="nav-links"><a href="/">Home</a><a href="/services/">Services</a><a href="/residential-pest-control/">Residential</a><a href="/commercial-pest-control/">Commercial</a><a href="/about/">About</a><a href="/blog/">Blogs</a><a href="/service-location/">Service Location</a><a href="/contact/">Contact</a></div>
    <a href="/contact/" class="nav-btn">Book Service</a>
    <button class="menu-btn" id="menuBtn" type="button" aria-label="Open navigation menu">☰</button>
</nav></header>
"""


def page_footer() -> str:
    return """<footer class="footer">
    <div class="footer-grid">
        <div class="footer-brand">
            <a href="/" class="logo">
                <div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" alt="Super Pest Control Services"></div>
                <div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div>
            </a>
            <p>Super Pest Control Services provides pest-management services for residential and commercial properties. Treatment recommendations and precautions depend on the pest and premises.</p>
            <div class="social-links" aria-label="Social media links">
                <a href="https://www.instagram.com/superpestcontrolservices?igsh=YzM3cmN0b2EwdGxh" target="_blank" rel="noopener" aria-label="Instagram"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="3" y="3" width="18" height="18" rx="5"></rect><circle cx="12" cy="12" r="4"></circle><circle cx="17.5" cy="6.5" r="1"></circle></svg></a>
                <a href="https://x.com/Superpestcontro" target="_blank" rel="noopener" aria-label="X"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 4l14 16M19 4L5 20"></path></svg></a>
                <a href="https://www.facebook.com/p/Super-Pest-Control-Services-100075474775254/" target="_blank" rel="noopener" aria-label="Facebook"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M14 21v-8h3l.5-3H14V8.2c0-.9.3-1.5 1.6-1.5H18V4.1c-.4-.1-1.3-.2-2.4-.2-2.4 0-4.1 1.5-4.1 4.2V10H9v3h2.5v8"></path></svg></a>
                <a href="https://www.linkedin.com/in/kishor-singh-10866a252/" target="_blank" rel="noopener" aria-label="LinkedIn"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M5 8v11M5 5.2v.1M10 19v-6.2a3 3 0 0 1 6 0V19M10 11v8M16 19v-6.2"></path></svg></a>
            </div>
        </div>
        <div class="footer-column"><h3>Explore Super Pest</h3>
            <a href="/">Super Pest Control home page</a>
            <a href="/services/">Pest control service list</a>
            <a href="/commercial-pest-control/">Commercial pest control and customer types</a>
            <a href="/about/">About Super Pest Control Services</a>
            <a href="/blog/">Pest management articles</a>
            <a href="/service-location/">Pest control service locations</a>
            <a href="/contact/">Contact Super Pest Control Services</a>
            <!-- BEGIN GENERATED LEGAL FOOTER LINKS --><a href="/privacy-policy/">Privacy Policy</a><a href="/terms-and-conditions/">Terms &amp; Conditions</a><!-- END GENERATED LEGAL FOOTER LINKS -->
        </div>
        <div class="footer-column"><h3>Services</h3>
            <a href="/services/termite-control/">Termite treatment services</a>
            <a href="/services/wood-borer-control/">Wood borer control services</a>
            <a href="/services/scorpion-control/">Scorpion control services</a>
            <a href="/services/general-pest-control/">General pest control services</a>
            <a href="/services/cockroach-control/">Cockroach control services</a>
            <a href="/services/rodent-management/">Rodent management services</a>
            <a href="/services/vector-control-fogging/">Vector control and fogging services</a>
            <a href="/services/bed-bug-eradication/">Bed bug eradication services</a>
            <a href="/services/commercial-fumigation/">Commercial fumigation services</a>
            <a href="/services/fly-management-systems/">Fly management services</a>
            <a href="/services/commercial-amc-ipm/">Commercial AMC and IPM services</a>
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
<a href="https://wa.me/917976572984" class="whatsapp" target="_blank" rel="noopener" aria-label="Chat with Super Pest Control Services on WhatsApp"><span>whatsapp</span></a>
<script src="/js/script.min.js?v=20260906" defer></script>
</body></html>
"""


def breadcrumb_html(items: list[tuple[str, str]], current: str) -> str:
    crumbs = [f'<li>{anchor(label, path)}</li>' for label, path in items]
    crumbs.append(f'<li aria-current="page">{esc(current)}</li>')
    return '<nav aria-label="Breadcrumb"><ol class="campaign-breadcrumb">' + "".join(crumbs) + "</ol></nav>"


def main_styles() -> str:
    return """<style>
.campaign-main{width:min(1060px,92%);margin:auto;padding:120px 0 72px;color:#334239;line-height:1.75}
.campaign-main .page-hero{min-height:32.5vh;width:100%;margin:0;padding:40px 0 0}
.campaign-main h1,.campaign-main h2,.campaign-main h3{color:#173e2e}
.campaign-main h1{font-family:Georgia,"Times New Roman",serif;font-size:clamp(30px,5vw,48px);font-weight:700;letter-spacing:-.02em;line-height:1.15}
.campaign-main h2{margin-top:38px;font-size:clamp(24px,3vw,32px)}
.campaign-main a{color:#245c3d;text-decoration:underline;text-underline-offset:3px}
.campaign-main .campaign-image{margin:28px 0;overflow:hidden;border-radius:16px;background:#eef2eb}
.campaign-main .campaign-image img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:cover}
.campaign-breadcrumb{display:flex;flex-wrap:wrap;gap:8px;list-style:none;padding:0;margin:18px auto;width:min(1060px,92%);font-size:14px}
.campaign-breadcrumb li+li:before{content:"/";margin-right:8px;color:#87918a}
.campaign-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:14px;padding:0;list-style:none}
.campaign-cards a{display:block;padding:16px;border:1px solid #e3ebe6;border-radius:12px;background:#fff;font-weight:700;text-decoration:none}
.campaign-main details{margin:12px 0;padding:16px 20px;border:1px solid #e3ebe6;border-radius:12px;background:#fff}
.campaign-main summary{color:#173e2e;font-weight:700;cursor:pointer}
.campaign-cta{padding:26px;border-radius:16px;background:#173e2e;color:#fff}
.campaign-cta h2,.campaign-cta p{color:#fff}
.campaign-cta a{display:inline-flex;margin:6px 12px 0 0;padding:10px 16px;border-radius:40px;background:#79b82a;color:#101610;font-weight:700;text-decoration:none}
.campaign-hi{padding:16px 20px;border-left:4px solid #79b82a;background:#f1f6ed}
.campaign-stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:24px 0}
.campaign-stats div{padding:18px 12px;border:1px solid #e3ebe6;border-radius:12px;background:#f5f7f2;text-align:center}
.campaign-stats strong{display:block;color:#173e2e;font-family:Georgia,"Times New Roman",serif;font-size:clamp(22px,3vw,30px);line-height:1.2}
.campaign-stats span{display:block;margin-top:5px;color:#526157;font-size:14px;font-weight:600}
@media(max-width:640px){.campaign-stats{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}}
@media(max-width:768px){.campaign-main{padding-top:96px}.campaign-main .page-hero{min-height:27.5vh;padding-top:32px}}
.campaign-district-services{width:min(1100px,92%);margin:28px auto;padding:24px;border-radius:14px;background:#f5f7f2}
</style>"""


def type_profile_map(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in data["customer_types"]}


def group1_faq(customer: dict[str, Any]) -> list[tuple[str, str]]:
    items = [(str(q), str(a)) for q, a in customer["faqs"]]
    if len(items) != 6:
        raise ValueError(f"{customer['id']} must have exactly six FAQs")
    return items


def render_customer_page(
    customer: dict[str, Any], city_pages: list[dict[str, Any]]
) -> tuple[str, str]:
    url_path = customer_path(customer)
    url = BASE_URL + url_path
    relevant = [item for item in city_pages if item["type"] == customer["id"]]
    districts = sorted({item["district"] for item in relevant})
    if not districts:
        districts = ["Jaipur", "Ajmer", "Alwar", "Kota"]
    faq_items = group1_faq(customer)
    breadcrumbs = [
        ("Home", "/"),
        ("Commercial Pest Control", "/commercial-pest-control/"),
    ]
    schema = schema_page(
        url,
        customer["title"],
        customer["description"],
        "Rajasthan",
        "Rajasthan",
        breadcrumbs + [(customer["name"], url_path)],
        faq_items,
    )
    city_links: list[str] = []
    for district in districts:
        city_links.append(
            f'<li>{anchor("Pest Control Services in " + district, district_path(district))}</li>'
        )
    for item in relevant:
        city_links.append(
            f'<li>{anchor(item["topic"] + " in " + item["area"], page_path(item))}</li>'
        )
    linked_services = sorted(
        {service for item in relevant for service in item["services"]}
        | set(customer.get("focused_services", []))
    )
    image_filename, image_alt = image_for_topic(customer["id"])
    stats = ""
    if customer["id"] == "industrial-sites":
        experience = approved_claim("experienceWording")
        experience_stat = (
            f"<div><strong>{esc(experience)}</strong></div>"
            if experience
            else ""
        )
        stats = (
            f'<section class="campaign-stats" aria-label="Super Pest Control experience">{experience_stat}</section>'
            if experience_stat
            else ""
        )
    content = f"""    {page_head(url,customer["title"],customer["description"],schema,image_filename)}
{main_styles()}
<main class="campaign-main">
{breadcrumb_html(breadcrumbs,customer["name"])}
<section class="page-hero"><span>WHO WE SERVE • RAJASTHAN</span><h1>{esc(customer["name"])} in Rajasthan</h1><p>Serving {esc(customer["short"])} premises across Rajasthan with inspection-led pest-management discussions.</p></section>
{stats}
<figure class="campaign-image"><img src="/images/{image_filename}" alt="{esc(image_alt)}" width="1200" height="675" loading="lazy"></figure>
<section><h2>Who this service is for</h2><p>{esc(customer["intro"])}</p></section>
<section><h2>Common pest concerns for {esc(customer["short"])} premises</h2><p>{esc(customer["context"])}</p></section>
<section><h2>Property operations and access</h2><p>{esc(customer["operations"])}</p></section>
{"<section><h2>Premises-specific coordination</h2><p>" + esc(customer["setting_note"]) + "</p></section>" if customer.get("setting_note") else ""}
<section><h2>Inspection and treatment planning</h2><p>{esc(customer["inspection"])}</p><p>The technician can explain the proposed scope, preparation, any access restriction and the instructions that apply after the selected service. The team should confirm those details before work is agreed; they are not identical for every property or pest.</p></section>
<section><h2>Timing and service coordination</h2><p>{esc(customer["timing"])}</p><p>Where a treatment cannot be coordinated safely with the operating schedule, discuss a different access window before confirming the appointment. A timing request is not a promise of a particular slot or uninterrupted operations.</p></section>
<section><h2>Prevention and practical follow-through</h2><p>{esc(customer["prevention"])}</p><p>After a visit, use the service-specific aftercare instructions and tell the provider if activity continues. Monitoring and a follow-up visit should be confirmed for the selected service rather than assumed from a general industry description.</p></section>
<section><h2>Child, guest, staff and pet safety</h2><p>Before treatment, disclose who uses the affected area, whether children or pets may be present, and any relevant site sensitivities. Protect food, equipment, personal belongings or stored goods as instructed for the chosen treatment. Keep people away from treated areas for the period specified by the service team and follow its re-entry, ventilation and cleaning guidance. There is no single safety procedure that applies to every pest or product.</p></section>
<section><h2>Scheduled service and documentation</h2><p>Businesses can ask about <a href="/services/commercial-amc-ipm/">Commercial AMC (IPM) for Rajasthan premises</a>. The existing service describes planned visits, monitoring and records. Ask which pests, locations, response arrangements and documents are included in the proposed written scope. Contract terms and follow-up depend on the agreed service and should be confirmed in writing.</p></section>
<section><h2>Related pest-management services</h2><p>Depending on the assessment, these existing services may be relevant:</p><ul class="campaign-cards">{service_links(linked_services or ["general-pest-control","commercial-amc-ipm"])}</ul></section>
<section><h2>Cities and local service pages</h2><p>Explore district coverage and the approved customer-type pages. City-specific service pages describe the verified service area and link back to this customer overview.</p><ul class="campaign-cards">{"".join(city_links)}</ul></section>
<section class="campaign-hi" lang="hi"><h2>राजस्थान में {esc(customer["name"])}</h2><p>सेवा का सही तरीका परिसर और कीट की स्थिति देखकर तय किया जाता है। निरीक्षण से पहले प्रभावित जगह, गतिविधि का समय और परिसर के कामकाज की जानकारी साझा करें।</p><p><strong>प्रश्न:</strong> उपचार से पहले सुरक्षा निर्देश कैसे जानें? चुनी गई सेवा और परिसर के लिए टीम से स्पष्ट निर्देश लें।</p></section>
<section><h2>Frequently asked questions</h2>{faq_html(faq_items)}</section>
<section class="campaign-cta"><h2>Discuss an assessment for your premises</h2><p>Share the property type, reported pest signs, affected area and access requirements with Super Pest Control Services.</p><a href="/contact/">Contact Super Pest Control Services</a><a href="tel:+919828066990">Call +91 98280-66990</a></section>
<!-- TODO: Add an owner-approved original photo or verified local example for this customer type. -->
</main>
{page_footer()}"""
    return content, url_path


def city_faq(
    item: dict[str, Any], specific_faqs: list[list[str]]
) -> list[tuple[str, str]]:
    district = item["district"]
    if len(specific_faqs) != 3:
        raise ValueError(f"{item['id']} must define three page-specific FAQs")
    return [(str(question), str(answer)) for question, answer in specific_faqs] + [
        (
            "What preparation is needed before treatment?",
            "Preparation depends on the service and property. Follow the instructions confirmed for the proposed treatment.",
        ),
        (
            "Does one pest report mean the entire premises needs treatment?",
            "No. The technician and customer should agree the areas in scope after reviewing the reported evidence.",
        ),
        (
            f"Can premises in {district} request recurring service?",
            "Ask about Commercial AMC (IPM) and confirm the included visits, services and records in the written proposal.",
        ),
    ]


def render_city_page(
    item: dict[str, Any],
    customer: dict[str, Any],
    rows: list[dict[str, str]],
    specific_faqs: list[list[str]],
) -> tuple[str, str]:
    url_path = page_path(item)
    url = BASE_URL + url_path
    row = area_row(item, rows)
    area = item["area"]
    district = item["district"]
    pest = item["topic"]
    if row:
        area_link = area_url(row, DISTRICT_DIRS)
        area_label = f"Pest Control in {area}, {district}"
        serving_line = (
            f"Serving {area}, {district} — PIN code {row['pin']}."
            if row["pin"]
            else f"Serving {area}, {district}."
        )
        schema_area = area
    else:
        area_link = ""
        area_label = ""
        serving_line = f"Serving customers in {district}, Rajasthan."
        schema_area = district
    faq_items = city_faq(item, specific_faqs)
    breadcrumbs = [
        ("Home", "/"),
        ("Commercial Pest Control", "/commercial-pest-control/"),
        (customer["name"], customer_path(customer)),
        (district, district_path(district)),
    ]
    schema_breadcrumbs = breadcrumbs + [(item["topic"] + " in " + area, url_path)]
    schema = schema_page(
        url,
        item["topic"] + " in " + area + " | Super Pest Control Services",
        item["topic"] + " serving " + area + ", " + district + ". Discuss an inspection, site-specific treatment and preparation guidance.",
        district,
        schema_area,
        schema_breadcrumbs,
        faq_items,
    )
    service_cards = "\n".join(
        f'<li>{anchor(SERVICE_LABELS[key][0] + " in Rajasthan", SERVICE_LABELS[key][1])}</li>'
        for key in item["services"]
    )
    related_links = [
        f'<li>{anchor(customer["name"] + " across Rajasthan", customer_path(customer))}</li>',
        f'<li>{anchor("Pest Control Services in " + district, district_path(district))}</li>',
    ]
    if area_link:
        related_links.append(f"<li>{anchor(area_label, area_link)}</li>")
    related_links.extend(
        f'<li>{anchor(SERVICE_LABELS[key][0] + " in Rajasthan", SERVICE_LABELS[key][1])}</li>'
        for key in item["services"][:3]
    )
    title = f'{item["topic"]} in {area} | Super Pest Control'
    description = (
        f'{item["topic"]} serving {area}, {district}. '
        "Discuss an inspection, site-specific treatment and preparation guidance."
    )
    if len(description) > 155:
        description = f'Pest control serving {area}, {district}. Request an inspection for {pest.lower()} and discuss access and preparation.'
    if len(description) > 155:
        description = description[:152].rsplit(" ", 1)[0].rstrip(" ,;:") + "."
    image_filename, image_alt = image_for_topic(item["topic"] + " " + customer["id"])
    content = f"""{page_head(url,title,description,schema,image_filename)}
{main_styles()}
<main class="campaign-main">
{breadcrumb_html(breadcrumbs,item["topic"] + " in " + area)}
<section class="page-hero"><span>{esc(district.upper())} • SERVICE FOR {esc(area.upper())}</span><h1>{esc(item["topic"])} in {esc(area)}</h1><p>{esc(serving_line)}</p></section>
<figure class="campaign-image"><img src="/images/{image_filename}" alt="{esc(image_alt)}" width="1200" height="675" loading="lazy"></figure>
<div data-similarity-content>
<section><h2>{esc(item["topic"])} serving {esc(area)}</h2><p>{esc(item["local"])}</p></section>
<section><h2>Service need and inspection focus</h2><p>{esc(item["focus"])}</p></section>
<section><h2>Planning an assessment for this service need</h2><p>{esc(item["plan"])}</p></section>
</div>
<p>Keep observations factual: note the location, time and material or space affected. An inspection helps distinguish a suspected pest from a confirmed identification and determine whether treatment is suitable.</p>
<section><h2>Relevant service options</h2><p>These existing service pages describe options that may be relevant after an assessment:</p><ul class="campaign-cards">{service_cards}</ul></section>
<section><h2>How to arrange access and treatment</h2><p>When you contact the team, identify who can authorize entry and describe occupancy, production, guest, cleaning or stock schedules that affect the area. The technician can discuss inspection access and the scope proposed for the reported signs. Ask which spaces are included and what preparation is needed before agreeing to treatment.</p><p>Timing, treatment method and follow-up depend on the pest identified, conditions at the site and the selected service. The technician should explain relevant precautions, restricted access and aftercare. Do not move potentially affected belongings or goods until the service team advises what to do.</p></section>
<section><h2>Safety and site preparation</h2><p>Tell the service team about children, pets, occupants, staff, food, sensitive materials and access limitations relevant to the affected area. Follow the instructions provided for the actual treatment, including any re-entry, ventilation or cleaning requirements. Keep people away from restricted spaces until the technician confirms access is appropriate. There is no universal preparation schedule for every pest or premises.</p></section>
<section><h2>Recurring support</h2><p>For a planned programme, ask about <a href="/services/commercial-amc-ipm/">Commercial AMC (IPM) in Rajasthan</a>. Confirm the agreed visit frequency, service categories, monitoring and documentation in the written scope.</p></section>
<section><h2>Related pages and services</h2><ul class="campaign-cards">{"".join(related_links)}</ul></section>
<section class="campaign-hi" lang="hi"><h2>{esc(area)} में {esc(item["topic"])}</h2><p>सेवा का दायरा जगह पर दिखे संकेत और परिसर की जरूरतों के अनुसार तय किया जाता है। निरीक्षण से पहले प्रभावित जगह और उपलब्ध समय की जानकारी दें।</p><p><strong>प्रश्न:</strong> उपचार से पहले क्या तैयारी करें? चुनी गई सेवा के लिए टीम से मिले निर्देशों का पालन करें।</p></section>
<section><h2>Frequently asked questions</h2>{faq_html(faq_items)}</section>
<section class="campaign-cta"><h2>Request an assessment serving {esc(area)}</h2><p>Share the pest concern, affected area and access window with Super Pest Control Services.</p><a href="/contact/">Contact Super Pest Control Services</a><a href="tel:+919828066990">Call +91 98280-66990</a></section>
<!-- TODO: Add a verified local example or original area photo after owner approval. -->
</main>
{page_footer()}"""
    return content, url_path


def district_section(
    district: str,
    items: list[dict[str, Any]],
) -> str:
    links = []
    for item in items:
        link_label = f'{item["topic"]} in {item["area"]}'
        link = anchor(link_label, page_path(item)).replace(
            "<a ",
            '<a style="display:block;padding:14px 18px;color:#173e2e;font-family:Georgia,\'Times New Roman\',serif;font-size:18px;line-height:1.45;font-weight:700;text-decoration:none;" ',
            1,
        )
        links.append(
            f'<li style="flex:0 1 320px;border:1px solid #e3ebe6;border-radius:10px;background:#fff;">{link}</li>'
        )
    return (
        f'{DISTRICT_START}<section class="campaign-district-services" aria-labelledby="customer-service-links" style="max-width:1060px;width:92%;margin:48px auto;padding:24px 0;text-align:center;">'
        f'<h2 id="customer-service-links">More services in {esc(district)}</h2>'
        f'<p>Explore focused pest-management information serving this district.</p>'
        f'<ul class="campaign-cards" style="display:flex;flex-wrap:wrap;justify-content:center;gap:14px;padding:0;list-style:none;">'
        f'{"".join(links)}</ul></section>{DISTRICT_END}'
    )


def commercial_customer_links(data: dict[str, Any]) -> str:
    cards = []
    for index, customer in enumerate(data["customer_types"], start=1):
        label = f'{customer["name"]} across Rajasthan'
        cards.append(
            f'<div><strong>{index:02}</strong><h3>{anchor(label, customer_path(customer))}</h3>'
            f'<p>Pest-management guidance for {esc(customer["short"])} premises.</p></div>'
        )
    return (
        f'{CUSTOMER_LINKS_START}<section class="section content-section" aria-labelledby="customer-types-heading">'
        f'<div><h2 id="customer-types-heading">Commercial services by customer type</h2>'
        '<p>Choose a customer-type page for practical pest-management considerations, relevant services and site-planning guidance.</p></div>'
        f'<div class="feature-list">{"".join(cards)}</div></section>{CUSTOMER_LINKS_END}'
    )


def replace_district_section(
    content: str, section: str, district: str
) -> str:
    if DISTRICT_START in content and DISTRICT_END in content:
        return re.sub(
            re.escape(DISTRICT_START) + r".*?" + re.escape(DISTRICT_END),
            section,
            content,
            count=1,
            flags=re.S,
        )
    match = re.search(r"</main>", content, re.I)
    if match is None:
        raise ValueError(f"Could not locate main closing tag in {district} district page")
    return content[: match.start()] + section + content[match.start() :]


def write_owned(path: Path, content: str, marker: str, write: bool) -> bool:
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if marker not in existing:
            raise ValueError(f"Refusing to overwrite an unowned page: {path}")
        if existing == content:
            return False
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="\n")
    return True


def update_sitemap(url_paths: set[str], write: bool) -> tuple[int, int, int]:
    tree = ET.parse(SITEMAP_FILE)
    root = tree.getroot()
    hub_url = f"{BASE_URL}/industries/"
    scorpion_url = f"{BASE_URL}/services/scorpion-control/"
    removed = 0
    corrected = 0
    for node in list(root.findall(f"{{{SITEMAP_NS}}}url")):
        location = node.findtext(f"{{{SITEMAP_NS}}}loc")
        if location == hub_url:
            root.remove(node)
            removed += 1
        elif location == scorpion_url:
            lastmod = node.find(f"{{{SITEMAP_NS}}}lastmod")
            if lastmod is not None and lastmod.text:
                sitemap_date = date.fromisoformat(lastmod.text[:10])
                if sitemap_date > date.today():
                    lastmod.text = date.today().isoformat()
                    corrected += 1
    present = {
        node.findtext(f"{{{SITEMAP_NS}}}loc")
        for node in root.findall(f"{{{SITEMAP_NS}}}url")
    }
    missing = sorted(f"{BASE_URL}{path}" for path in url_paths if f"{BASE_URL}{path}" not in present)
    for url in missing:
        node = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
        ET.SubElement(node, f"{{{SITEMAP_NS}}}loc").text = url
        ET.SubElement(node, f"{{{SITEMAP_NS}}}lastmod").text = date.today().isoformat()
    if write and (missing or removed or corrected):
        tree.write(SITEMAP_FILE, encoding="UTF-8", xml_declaration=True)
    return len(missing), removed, corrected


def replace_commercial_customer_links(
    content: str, section: str
) -> str:
    if CUSTOMER_LINKS_START in content and CUSTOMER_LINKS_END in content:
        return re.sub(
            re.escape(CUSTOMER_LINKS_START) + r".*?" + re.escape(CUSTOMER_LINKS_END),
            section,
            content,
            count=1,
            flags=re.S,
        )
    heading = re.search(r"<h2\b[^>]*>\s*Industries We Serve\s*</h2>", content, re.I)
    if heading is None:
        raise ValueError("Could not locate the Industries We Serve section in Commercial page")
    closing = re.search(r"</section\s*>", content[heading.end() :], re.I)
    if closing is None:
        raise ValueError("Could not locate the Commercial customer section boundary")
    end = heading.end() + closing.end()
    opening = content.rfind("<section", 0, heading.start())
    if opening < 0:
        raise ValueError("Could not locate the Commercial customer section start")
    return content[:opening] + section + content[end:]


def visible_main(page: str) -> str:
    page = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    page = re.sub(r"(?is)<header\b.*?</header>|<footer\b.*?</footer>", " ", page)
    page = re.sub(r"(?s)<!--.*?-->", " ", page)
    return " ".join(words(html.unescape(re.sub(r"<[^>]+>", " ", page))))


def page_metadata(page: str) -> dict[str, str]:
    def one(pattern: str, field: str) -> str:
        match = re.search(pattern, page, re.I | re.S)
        if match is None:
            raise ValueError(f"Missing {field}")
        return html.unescape(match.group(1).strip())

    return {
        "title": one(r"<title>(.*?)</title>", "title"),
        "description": one(r'<meta name="description" content="(.*?)"', "description"),
        "canonical": one(r'<link rel="canonical" href="(.*?)"', "canonical"),
        "h1": one(r"<h1[^>]*>(.*?)</h1>", "H1"),
    }


def validate_campaign(
    generated: list[tuple[str, str, str]],
    all_url_paths: set[str],
) -> None:
    current_metadata: dict[str, list[str]] = {
        "title": [],
        "description": [],
        "h1": [],
        "canonical": [],
    }
    new_texts: list[tuple[str, str]] = []
    for path, content, label in generated:
        metadata = page_metadata(content)
        if len(re.findall(r"<h1(?:\s|>)", content, re.I)) != 1:
            raise ValueError(f"{label}: expected exactly one H1")
        if len(metadata["description"]) > 160:
            raise ValueError(f"{label}: meta description exceeds 160 characters")
        if metadata["canonical"] != BASE_URL + path:
            raise ValueError(f"{label}: canonical mismatch")
        if not re.search(r"<meta property=\"og:title\"", content) or not re.search(
            r"<meta name=\"twitter:title\"", content
        ):
            raise ValueError(f"{label}: missing social metadata")
        main_text = visible_main(content)
        if path.startswith("/pest-control-for-") and len(main_text.split()) < 700:
            raise ValueError(
                f"{label}: customer page has only {len(main_text.split())} visible words"
            )
        jsonld_matches = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', content, re.S
        )
        for script in jsonld_matches:
            json.loads(script)
        if path != "/industries/" and not any(
            '"@type":"BreadcrumbList"' in item for item in jsonld_matches
        ):
            raise ValueError(f"{label}: missing BreadcrumbList schema")
        if path != "/industries/" and not any(
            '"@type":"FAQPage"' in item for item in jsonld_matches
        ):
            raise ValueError(f"{label}: missing FAQPage schema")
        for key in current_metadata:
            current_metadata[key].append(metadata[key])
        for href in re.findall(r'<a\b[^>]*href="(/[^"]*)"', content, re.I):
            target = href.split("#", 1)[0]
            if target and target not in all_url_paths:
                local = ROOT / target.lstrip("/") / "index.html"
                if not local.is_file():
                    raise ValueError(f"{label}: broken internal link {href}")
        if re.search(
            r"(?is)<a\b[^>]*>\s*(?:click here|read more|learn more|more|view|here|details|know more)\s*</a>",
            content,
        ):
            raise ValueError(f"{label}: generic anchor text found")
        if re.search(r"\b(?:FSSAI|HACCP|NABH|ISO\s*\d*|certified|certification|licen[cs]e number)\b", main_text, re.I):
            raise ValueError(f"{label}: unsupported compliance or certification claim")
        if re.search(r"\b(?:HDFC|ICICI|SBI|Axis Bank|Kotak)\b", main_text, re.I):
            raise ValueError(f"{label}: bank-name text is not allowed")
        similarity_content = re.search(
            r'<div data-similarity-content>(.*?)</div>',
            content,
            re.S,
        )
        comparison_text = (
            visible_main(similarity_content.group(1))
            if similarity_content
            else main_text
        )
        new_texts.append((label, comparison_text))
    for key, values in current_metadata.items():
        repeated = [value for value, count in Counter(values).items() if count > 1]
        if repeated:
            raise ValueError(f"Duplicate new-page {key}: {repeated[0]}")
    similarities = []
    for index, (label_a, text_a) in enumerate(new_texts):
        for label_b, text_b in new_texts[index + 1 :]:
            score = difflib.SequenceMatcher(
                None, text_a.casefold().split(), text_b.casefold().split(), autojunk=False
            ).ratio()
            if score > 0.60:
                similarities.append((label_a, label_b, score))
    if similarities:
        pairs = ", ".join(
            f"{a} ↔ {b} ({score:.0%})" for a, b, score in sorted(similarities, key=lambda x: -x[2])
        )
        raise ValueError(f"Text similarity exceeds 60%: {pairs}")


def run(write: bool, workbook: Path) -> int:
    global ARGS
    ARGS.workbook = workbook
    data, rows = load_source()
    customers = type_profile_map(data)
    cities = data["city_pages"]
    routes: set[str] = set()
    generated: list[tuple[str, str, str]] = []
    outputs: list[tuple[Path, str, str]] = []

    for customer in data["customer_types"]:
        content, path = render_customer_page(customer, cities)
        content = apply_main_footer(content)
        content = content.replace(
            "<body>",
            f"<body>\n{PAGE_MARKER} {path} -->",
            1,
        )
        outputs.append((ROOT / path.strip("/") / "index.html", content, PAGE_MARKER))
        generated.append((path, content, customer["name"]))
        routes.add(path)

    for item in cities:
        content, path = render_city_page(
            item, customers[item["type"]], rows, data["city_faqs"][item["id"]]
        )
        content = apply_main_footer(content)
        content = content.replace(
            "<body>",
            f"<body>\n{PAGE_MARKER} {path} -->",
            1,
        )
        outputs.append((ROOT / path.strip("/") / "index.html", content, PAGE_MARKER))
        generated.append((path, content, item["id"]))
        routes.add(path)

    all_url_paths = set(routes)
    for file_path in ROOT.rglob("index.html"):
        relative = file_path.parent.relative_to(ROOT).as_posix()
        all_url_paths.add("/" + relative.rstrip("/") + "/" if relative != "." else "/")

    validate_campaign(generated, all_url_paths)

    # Ensure every customer and city destination is linked from its source context.
    for customer in data["customer_types"]:
        matching = [item for item in cities if item["type"] == customer["id"]]
        page = next(content for path, content, _ in generated if path == customer_path(customer))
        for item in matching:
            if page_path(item) not in page:
                raise ValueError(f"Orphan city page from customer page: {item['id']}")
    for item in cities:
        if customer_path(customers[item["type"]]) not in next(
            content for path, content, _ in generated if path == page_path(item)
        ):
            raise ValueError(f"City page does not link to its customer page: {item['id']}")

    if not write:
        for _, _, label in generated:
            print(f"Validated preview: {label}")
        print(f"Validated {len(generated)} pages; no files written.")
        return 0

    page_changes = sum(
        write_owned(file_path, content, marker, write=True)
        for file_path, content, marker in outputs
    )

    # Remove the retired Industries destination from existing page navigation.
    nav_changes = 0
    for file_path in ROOT.rglob("index.html"):
        old = file_path.read_text(encoding="utf-8")
        updated = replace_nav(old)
        if updated != old:
            file_path.write_text(updated, encoding="utf-8", newline="\n")
            nav_changes += 1

    # Keep the existing service-area generator's future page headers consistent.
    area_generator = ROOT / "tools" / "generate_service_areas.py"
    generator_text = area_generator.read_text(encoding="utf-8")
    old_nav = '<a href="/commercial-pest-control/">Commercial</a><a href="/industries/">Industries</a><a href="/about/">About</a>'
    new_nav = '<a href="/commercial-pest-control/">Commercial</a><a href="/about/">About</a>'
    if old_nav in generator_text:
        area_generator.write_text(generator_text.replace(old_nav, new_nav), encoding="utf-8")

    commercial_path = ROOT / "commercial-pest-control" / "index.html"
    commercial_old = commercial_path.read_text(encoding="utf-8")
    commercial_updated = replace_commercial_customer_links(
        commercial_old, commercial_customer_links(data)
    )
    if commercial_updated != commercial_old:
        commercial_path.write_text(commercial_updated, encoding="utf-8", newline="\n")

    district_groups: dict[str, list[dict[str, Any]]] = {}
    district_changes = 0
    for item in cities:
        district_groups.setdefault(item["district"], []).append(item)
    for district, items in district_groups.items():
        path = ROOT / f"pest-control-in-{district_path_slug(district)}" / "index.html"
        old = path.read_text(encoding="utf-8")
        section = district_section(district, items)
        updated = replace_district_section(old, section, district)
        if updated != old:
            path.write_text(updated, encoding="utf-8", newline="\n")
            district_changes += 1

    added, removed, corrected = update_sitemap(routes, write=True)
    print(f"Created/updated {page_changes} generated page files.")
    print(f"Updated existing navigation on {nav_changes} pages.")
    print("Moved all 9 customer-type links into the Commercial page.")
    print(f"Updated district links on {district_changes} district pages.")
    print(f"Added {added} sitemap URLs.")
    print(f"Removed {removed} Industries hub sitemap URLs.")
    print(f"Corrected {corrected} future Scorpion sitemap dates.")
    for path, _, label in generated:
        print(f"{path} — {label}")
    return 0


class _Args:
    workbook: Path


ARGS = _Args()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", required=True, type=Path)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write generated pages, navigation, district links and sitemap entries",
    )
    args = parser.parse_args()
    if not args.workbook.is_file():
        parser.error(f"Workbook not found: {args.workbook}")
    try:
        return run(args.write, args.workbook)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as error:
        print(f"Generation stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
