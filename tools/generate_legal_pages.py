#!/usr/bin/env python3
"""Generate the site's legal information pages and add footer-only links."""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.site_footer import apply_main_footer
from tools.site_schema import website_schema

BASE_URL = "https://www.superpest.in"
SITEMAP_URL = "https://www.superpest.in"
SITEMAP = ROOT / "sitemap.xml"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
ROBOTS = "index, follow"
FOOTER_START = "<!-- BEGIN GENERATED LEGAL FOOTER LINKS -->"
FOOTER_END = "<!-- END GENERATED LEGAL FOOTER LINKS -->"
FOOTER_LINKS = (
    f"{FOOTER_START}<a href=\"/privacy-policy/\">Privacy Policy</a>"
    f"<a href=\"/terms-and-conditions/\">Terms &amp; Conditions</a>{FOOTER_END}"
)

PRIVACY_SECTIONS = [
    ("introduction", "Introduction", """
<p>Super Pest Control Services ("we", "us", "our") provides pest control and related services in Rajasthan, India. This Privacy Policy explains what personal information we collect when you visit superpest.in (the "Website"), contact us, or book our services, how we use it, and the choices you have. By using the Website or sharing your information with us, you agree to the practices described here.</p>"""),
    ("information-we-collect", "Information We Collect", """
<h3>Information you give us</h3>
<ul><li><strong>Contact details:</strong> your name, phone number, email address and WhatsApp number.</li>
<li><strong>Service details:</strong> the address or location of the property, type of property (home, office, hotel, hostel, warehouse, factory, etc.), the pest problem, preferred date and time, and any message or photos you send us.</li>
<li><strong>Billing details:</strong> name, address, and (if you request a GST invoice) your GST number and business name, as needed for invoicing and payment records.</li></ul>
<h3>Information collected automatically</h3>
<p>Technical data such as IP address, browser type, device type, pages visited, time spent, and referring website may be collected by the Website or its hosting infrastructure.</p>
<h3>Information from calls and messages</h3>
<p>When you call or message us (including on WhatsApp), we may keep a record of the conversation to follow up on your request and improve our service.</p>
<p>We do not knowingly collect sensitive personal data such as passwords, card numbers or bank login details through the Website forms.</p>"""),
    ("how-we-use-information", "How We Use Your Information", """
<p>We use your information to:</p>
<ul><li>Respond to your enquiries and provide quotations.</li>
<li>Schedule, carry out and follow up on pest control services.</li>
<li>Prepare invoices, receive payments and keep business records.</li>
<li>Send service reminders, follow-up visits and relevant service updates.</li>
<li>Improve our Website, services and customer support.</li>
<li>Prevent misuse and fraud, and comply with legal obligations.</li>
<li>Send promotional messages about our services only where you have agreed, or where the law allows. You can opt out at any time.</li></ul>"""),
    ("consent-and-legal-basis", "Consent and Legal Basis", """
<p>We process your personal information based on your consent (for example, when you submit a form or contact us), to perform a service you have requested, and to meet legal and accounting requirements under applicable Indian law, including the Information Technology Act, 2000 and the Digital Personal Data Protection Act, 2023. You may withdraw your consent at any time by contacting us (see Contact and Grievance). Withdrawal does not affect processing already carried out, and we may not be able to provide certain services without the information needed to perform them.</p>"""),
    ("sharing-of-information", "Sharing of Information", """
<p>We do not sell your personal information. We may share it only with:</p>
<ul><li>Our own technicians and staff who need it to carry out your service.</li>
<li>Service providers who help us operate the Website and business, such as hosting, analytics, communication and payment providers, only as needed for their services and under appropriate confidentiality obligations.</li>
<li>Government or legal authorities when required by law, court order or to protect our legal rights.</li>
<li>A successor, in case of a merger, sale or transfer of our business, subject to this Policy.</li></ul>"""),
    ("cookies-and-analytics", "Cookies and Analytics", """
<p>The Website may use cookies and similar technologies to make the site work, remember preferences and understand how visitors use it. The site pages reviewed contain a Google Maps embed on the Jaipur district page and links to WhatsApp and social media platforms. We did not find Google Analytics, Google Tag Manager or Meta Pixel tags in the HTML reviewed. Third-party embeds and services may process information under their own privacy practices.</p>
<p>You can control or delete cookies through your browser settings. Disabling cookies may affect some Website features.</p>"""),
    ("third-party-services", "Third-Party Websites and Services", """
<p>The Website may link to third-party services such as WhatsApp, Google Maps and social media platforms. These have their own privacy practices, and we are not responsible for their content or policies. Please read their policies before sharing information with them.</p>"""),
    ("data-retention", "Data Retention", """
<p>We keep personal information only as long as needed for the purposes described above, including service follow-ups, accounting and legal requirements. When it is no longer needed, we delete or anonymise it.</p>"""),
    ("data-security", "Data Security", """
<p>We take reasonable technical and organisational steps to protect your information against unauthorised access, loss or misuse. However, no method of transmission over the internet or electronic storage is completely secure, so we cannot guarantee absolute security.</p>"""),
    ("your-rights", "Your Rights", """
<p>Subject to applicable law, you may:</p>
<ul><li>Ask to access the personal information we hold about you.</li>
<li>Ask us to correct inaccurate or incomplete information.</li>
<li>Ask us to delete your information, where it is no longer needed.</li>
<li>Withdraw your consent, or opt out of promotional messages.</li>
<li>Raise a grievance about how your information is handled.</li></ul>
<p>To exercise these rights, contact us using the details in Contact and Grievance. We may need to verify your identity before acting on a request.</p>"""),
    ("children", "Children", """
<p>The Website is intended for adults. We do not knowingly collect personal information from children. If you believe a child has given us personal information, please contact us and we will delete it.</p>"""),
    ("contact-and-grievance", "Contact and Grievance", """
<p>For questions, requests or complaints about this Privacy Policy or your personal information, contact:</p>
<address>Super Pest Control Services<br>
Address: 82/270, Sector-8, Pratap Nagar, Sanganer, Jaipur, Rajasthan 302033<br>
Phone: +91 98280 66990 or +91 79765 72984<br>
Email: <a href="mailto:superpestcontrolservices.jaipur@gmail.com">superpestcontrolservices.jaipur@gmail.com</a><br>
Grievance contacts: Kishore Singh Chouhan, Owner; Vijendra Chouhan, Managing Director</address>
<p>We aim to acknowledge requests within 7 days and resolve them within a reasonable time as required by law.</p>"""),
    ("changes-to-policy", "Changes to This Policy", """
<p>We may update this Privacy Policy from time to time. The latest version will always be on this page with the "Last updated" date. Please check it periodically. Continued use of the Website after changes means you accept the updated Policy.</p>"""),
]

TERMS_SECTIONS = [
    ("acceptance-of-terms", "Acceptance of Terms", """
<p>These Terms &amp; Conditions ("Terms") apply to your use of superpest.in (the "Website") and to any pest control or related services ("Services") provided by Super Pest Control Services ("we", "us", "our"). By using the Website, requesting a quote or booking a Service, you agree to these Terms. If you do not agree, please do not use the Website or our Services.</p>"""),
    ("about-our-services", "About Our Services", """
<p>We provide pest control and related services, which may include termite control, general pest control, rodent management, vector control and fogging, bed bug treatment, wood borer control, fumigation, fly management, sanitisation and annual maintenance contracts (AMC) for homes, offices, hotels, hostels, restaurants, warehouses, factories and other premises. Information on the Website is general and for guidance only. The exact treatment, products, quantity and number of visits are decided after inspecting your property and are confirmed in your quotation or service agreement.</p>"""),
    ("service-areas", "Service Areas and Availability", """
<p>Locations, districts and areas listed on the Website show where we aim to serve. Listing a location does not guarantee availability for every request. Availability depends on scheduling, distance, the type of job and local conditions. We will confirm whether we can serve your location when you contact us.</p>"""),
    ("quotations-and-pricing", "Quotations and Pricing", """
<p>Any price shown or discussed before inspection is an estimate. The final quotation is given after assessing the property, pest type, infestation level, area and service required. Quotations are valid for 15 days unless stated otherwise. Applicable taxes, such as GST, are extra unless stated in the quotation.</p>"""),
    ("booking-rescheduling-cancellation", "Booking, Rescheduling and Cancellation", """
<p>A booking is confirmed when we confirm the date and time with you by phone, WhatsApp, message or email. Please give 2 to 3 days' notice before the scheduled service day to reschedule or cancel. Cancellation charges of up to 50% of the service cost may apply. We may reschedule a visit because of weather, safety, access problems or other circumstances beyond our control, and we will inform you as soon as possible.</p>"""),
    ("customer-responsibilities", "Customer Responsibilities", """
<p>To help us deliver safe and effective Services, you agree to:</p>
<ul><li>Provide accurate information about the property and the pest problem.</li>
<li>Ensure safe access to all areas that need treatment, and that an adult authorised person is present when required.</li>
<li>Tell us before the treatment about children, elderly persons, pregnant women, people with allergies or breathing problems, pets, aquariums, and any medical or special conditions at the property.</li>
<li>Prepare the premises as instructed (for example covering or removing food, utensils, water storage, aquariums, and moving furniture when asked).</li>
<li>Follow our post-treatment instructions, including re-entry time, ventilation, cleaning and any follow-up advice.</li>
<li>Maintain hygiene, repair leaks or structural problems, and manage waste and food storage, because these affect the success of pest control.</li></ul>"""),
    ("safety-and-products", "Safety and Products", """
<p>Our Services are carried out by trained personnel, using products and methods suited to the job and applied according to the product label and safety directions. Please keep children, pets and unauthorised persons away from treated areas for the time advised by our technician. In an emergency or if you suspect a reaction, contact a doctor or the nearest hospital, and inform us as soon as possible.</p>"""),
    ("service-warranty", "Service Warranty and Re-treatment", """
<p>Any warranty, follow-up or re-treatment period applies only if it is stated in your written quotation, invoice or service agreement. Warranty terms, if any, are stated in the quotation for each service. A warranty or re-treatment may not apply if the problem arises from reasons outside our control, such as structural defects, water leakage, renovation or construction after treatment, failure to follow our instructions, treatment or interference by another party, or re-infestation from neighbouring properties. Warranty is void if payment is pending.</p>"""),
    ("payments", "Payments", """
<p>Payment is due as stated in the quotation or invoice. Accepted payment methods will be confirmed at the time of booking. For AMC and contract services, payment terms are as written in the contract. We may pause or cancel Services if payment is overdue.</p>"""),
    ("results-and-limitations", "Results and Limitations", """
<p>Pests are living organisms, and results depend on many factors, including the type of pest, the infestation level, building condition, hygiene and surroundings. We use professional methods to control pests, but we cannot guarantee that a property will remain completely pest-free at all times. Some pests may need more than one visit or follow-up treatments.</p>"""),
    ("limitation-of-liability", "Limitation of Liability", """
<p>To the extent permitted by law, we are not liable for indirect, incidental or consequential loss, or for loss caused by incorrect or incomplete information, restricted access, failure to follow our instructions, pre-existing damage or conditions, or events beyond our reasonable control. Our total liability for any claim relating to a Service is limited to the amount you paid us for that Service. Nothing in these Terms limits any right you have under applicable consumer protection law, including the Consumer Protection Act, 2019.</p>"""),
    ("website-use", "Website Use and Intellectual Property", """
<p>You may use the Website for lawful purposes only. You must not copy, scrape, reproduce or misuse the Website content, text, images, logos or design for commercial purposes without our written permission. All content on the Website belongs to Super Pest Control Services or its licensors and is protected by applicable law.</p>"""),
    ("third-party-links", "Third-Party Links", """
<p>The Website may link to third-party websites or services. We do not control them and are not responsible for their content or practices.</p>"""),
    ("force-majeure", "Force Majeure", """
<p>We are not responsible for delay or failure to perform Services caused by events beyond our reasonable control, including severe weather, natural disasters, strikes, curfews, government orders, outages or health emergencies.</p>"""),
    ("privacy", "Privacy", """
<p>Our handling of personal information is described in the Privacy Policy available on this Website.</p>"""),
    ("governing-law", "Governing Law and Jurisdiction", """
<p>These Terms are governed by the laws of India. Courts at Jaipur, Rajasthan shall have jurisdiction over any dispute, subject to any rights you have under applicable consumer protection law.</p>"""),
    ("changes-to-terms", "Changes to These Terms", """
<p>We may update these Terms from time to time. The latest version will always be on this page with the "Last updated" date. Continued use of the Website or Services after changes means you accept the updated Terms.</p>"""),
    ("contact-us", "Contact Us", """
<address>Super Pest Control Services<br>
Address: 82/270, Sector-8, Pratap Nagar, Sanganer, Jaipur, Rajasthan 302033<br>
Phone: +91 98280 66990 or +91 79765 72984<br>
Email: <a href="mailto:superpestcontrolservices.jaipur@gmail.com">superpestcontrolservices.jaipur@gmail.com</a></address>"""),
]


def render_page(
    page_path: str,
    title: str,
    description: str,
    sections: list[tuple[str, str, str]],
) -> str:
    url = BASE_URL + page_path
    toc = "\n".join(
        f'<li><a href="#{html.escape(section_id)}">{html.escape(heading)}</a></li>'
        for section_id, heading, _ in sections
    )
    section_html = "\n".join(
        f'<section id="{html.escape(section_id)}"><h2>{html.escape(heading)}</h2>{body}</section>'
        for section_id, heading, body in sections
    )
    crumb_name = title.split(" | ", 1)[0]
    jsonld_data = {
        "@context": "https://schema.org",
        "@graph": [
            website_schema(),
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
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": f"{BASE_URL}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": crumb_name,
                        "item": url,
                    },
                ],
            },
        ],
    }
    jsonld = (
        '<script type="application/ld+json">\n'
        + json.dumps(jsonld_data, ensure_ascii=False, indent=2)
        + "\n</script>"
    )
    page_html = f"""<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <meta name="description" content="{html.escape(description, quote=True)}">
    <meta name="robots" content="{ROBOTS}">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{html.escape(title, quote=True)}">
    <meta property="og:description" content="{html.escape(description, quote=True)}">
    <meta property="og:url" content="{url}">
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{html.escape(title, quote=True)}">
    <meta name="twitter:description" content="{html.escape(description, quote=True)}">
    {jsonld}
    <link rel="icon" type="image/webp" href="/images/Logooo.webp">
    <link rel="stylesheet" href="/css/style.min.css?v=20261024-4" fetchpriority="high">
    <style>
        .legal-main{{width:min(800px,92%);margin:0 auto;padding:120px 0 72px;color:#334239;line-height:1.75}}
        .legal-main h1,.legal-main h2,.legal-main h3{{color:#173e2e}}
        .legal-main h1{{font-family:Georgia,"Times New Roman",serif;font-size:clamp(32px,5vw,48px);line-height:1.15}}
        .legal-main h2{{margin:34px 0 10px;font-size:clamp(22px,3vw,30px)}}
        .legal-main h3{{margin:20px 0 6px;font-size:18px}}
        .legal-main p,.legal-main ul,.legal-main address{{margin:10px 0}}
        .legal-main ul{{padding-left:24px}}
        .legal-main address{{font-style:normal}}
        .legal-main a{{color:#245c3d;text-decoration:underline;text-underline-offset:3px}}
        .legal-breadcrumb{{display:flex;gap:8px;list-style:none;padding:0;margin:0 0 18px;font-size:14px}}
        .legal-toc{{padding:18px 22px;border:1px solid #e3ebe6;border-radius:12px;background:#f5f7f2}}
        .legal-toc h2{{margin:0 0 8px;font-size:20px}}
        .legal-updated{{color:#526157;font-size:14px}}
        @media(max-width:768px){{.legal-main{{padding-top:96px}}}}
    </style>
</head>
<body>
<header class="header"><nav class="navbar" aria-label="Main navigation">
    <a href="/" class="logo"><div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" loading="eager" alt="Super Pest Control Services"></div><div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div></a>
    <div class="nav-links"><a href="/">Home</a><a href="/services/">Services</a><a href="/residential-pest-control/">Residential</a><a href="/commercial-pest-control/">Commercial</a><a href="/about/">About</a><a href="/blog/">Blogs</a><a href="/service-location/">Service Location</a><a href="/contact/">Contact</a></div>
    <a href="/contact/" class="nav-btn">Book Service</a>
    <button class="menu-btn" id="menuBtn" type="button" aria-label="Open navigation menu">☰</button>
</nav></header>
<main class="legal-main">
    <nav aria-label="Breadcrumb"><ol class="legal-breadcrumb"><li><a href="/">Home</a></li><li aria-current="page">{html.escape(crumb_name)}</li></ol></nav>
    <h1>{html.escape(crumb_name)}</h1>
    <p class="legal-updated">Last updated: {date.today().isoformat()}</p>
    <nav class="legal-toc" aria-label="Table of contents"><h2>Contents</h2><ol>{toc}</ol></nav>
    {section_html}
</main>
<footer class="footer"><div class="footer-grid">
    <div class="footer-brand"><a href="/" class="logo"><div class="logo-mark"><img src="/images/logo-42.webp" width="42" height="41" loading="lazy" alt="Super Pest Control Services"></div><div class="logo-text"><strong>SUPER PEST</strong><small>CONTROL SERVICES</small></div></a><p>Super Pest Control Services</p></div>
    <div class="footer-column"><h3>Quick Links</h3><a href="/">Home</a><a href="/services/">Services</a><a href="/about/">About</a><a href="/blog/">Blog</a><a href="/service-location/">Service Location</a><a href="/contact/">Contact</a>{FOOTER_LINKS}</div>
    <div class="footer-column"><h3>Services</h3><a href="/services/termite-control/">Termite Control</a><a href="/services/general-pest-control/">General Pest Control</a><a href="/services/rodent-management/">Rodent Management</a><a href="/services/cockroach-control/">Cockroach Control</a><a href="/services/wasp-hornet-nest-removal/">Wasp &amp; Hornet Nest Removal</a><a href="/contact/">Any Other Pests?</a></div>
    <div class="footer-column"><h3>Contact</h3><p>+91 98280 66990</p><p>+91 79765 72984</p><p>superpestcontrolservices.jaipur@gmail.com</p><p>Jaipur, Rajasthan</p></div>
</div><div class="footer-bottom"><p>© 2026 Super Pest Control Services. All Rights Reserved.</p></div></footer>
<script src="/js/script.min.js?v=20260906" defer></script>
</body>
</html>
"""
    return apply_main_footer(page_html)


def add_footer_links(page: str, path: Path) -> str:
    page = re.sub(
        re.escape(FOOTER_START) + r".*?" + re.escape(FOOTER_END),
        "",
        page,
        flags=re.S,
    )
    footer_match = re.search(r"<footer\b.*?</footer>", page, re.I | re.S)
    if footer_match is None:
        raise ValueError(f"Could not locate footer in {path}")
    footer = footer_match.group()
    for href in ("/privacy-policy/", "/terms-and-conditions/"):
        footer = re.sub(
            r'<a\b(?=[^>]*href=["\']'
            + re.escape(href)
            + r'["\'])[^>]*>.*?</a>',
            "",
            footer,
            flags=re.I | re.S,
        )
    page = page[: footer_match.start()] + footer + page[footer_match.end() :]
    pattern = re.compile(
        r'(<div\b[^>]*class="footer-column"[^>]*>\s*<h3>\s*(?:Quick Links|Explore Super Pest|Explore)\s*</h3>.*?)(</div>)',
        re.I | re.S,
    )
    matches = list(pattern.finditer(page))
    if len(matches) != 1:
        raise ValueError(f"Expected one Quick Links footer column in {path}; found {len(matches)}")
    match = matches[0]
    return page[: match.end(1)] + FOOTER_LINKS + page[match.start(2) :]


def update_sitemap(write: bool) -> int:
    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    entries = {
        f"{SITEMAP_URL}/privacy-policy/": 0.3,
        f"{SITEMAP_URL}/terms-and-conditions/": 0.3,
    }
    loc_tag = f"{{{SITEMAP_NS}}}loc"
    priority_tag = f"{{{SITEMAP_NS}}}priority"
    count = 0
    existing = {
        node.findtext(loc_tag): node for node in root.findall(f"{{{SITEMAP_NS}}}url")
    }
    for url, priority in entries.items():
        node = existing.get(url)
        if node is None:
            node = ET.SubElement(root, f"{{{SITEMAP_NS}}}url")
            ET.SubElement(node, loc_tag).text = url
            ET.SubElement(node, f"{{{SITEMAP_NS}}}lastmod").text = date.today().isoformat()
            ET.SubElement(node, priority_tag).text = str(priority)
            count += 1
        else:
            priority_node = node.find(priority_tag)
            if priority_node is None:
                priority_node = ET.SubElement(node, priority_tag)
            priority_node.text = str(priority)
    if write:
        tree.write(SITEMAP, encoding="UTF-8", xml_declaration=True)
    return count


def generate(write: bool) -> int:
    pages = {
        "/privacy-policy/": (
            "Privacy Policy | Super Pest Control Services",
            "Learn how Super Pest Control Services collects, uses, protects and retains personal information when you visit our website or contact us.",
            PRIVACY_SECTIONS,
        ),
        "/terms-and-conditions/": (
            "Terms & Conditions | Super Pest Control Services",
            "Read the terms for using the Super Pest Control Services website, requesting quotations and booking pest-management services.",
            TERMS_SECTIONS,
        ),
    }
    for route, (title, description, sections) in pages.items():
        path = ROOT / route.strip("/") / "index.html"
        rendered = render_page(route, title, description, sections)
        if not path.exists() or path.read_text(encoding="utf-8") != rendered:
            if write:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(rendered, encoding="utf-8", newline="\n")
            print(f"{'Generated' if write else 'Would generate'} {route}")

    changed = 0
    for path in ROOT.rglob("*.html"):
        old = path.read_text(encoding="utf-8")
        updated = add_footer_links(old, path)
        if updated != old:
            changed += 1
            if write:
                path.write_text(updated, encoding="utf-8", newline="\n")
    if write:
        print(f"Updated footer links in {changed} existing HTML pages.")
    else:
        print(f"Would update footer links in {changed} HTML pages.")

    added = update_sitemap(write)
    print(f"{'Added' if write else 'Would add'} {added} sitemap entries.")
    return 0


def report_placeholders() -> int:
    found = 0
    for path in sorted(ROOT.rglob("*.html")):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if "[[TO-FILL" in line:
                print(f"{path.relative_to(ROOT)}:{line_number}: {line.strip()}")
                found += 1
    print(f"Remaining placeholder lines: {found}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write pages, footers and sitemap changes")
    parser.add_argument("--check-placeholders", action="store_true", help="List remaining TO-FILL markers")
    args = parser.parse_args()
    try:
        if args.check_placeholders:
            return report_placeholders()
        return generate(args.write)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Legal page generation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
