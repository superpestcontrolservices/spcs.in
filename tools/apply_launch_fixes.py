#!/usr/bin/env python3
"""Apply idempotent launch-readiness updates to generated static pages."""

from __future__ import annotations

import csv
import html
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIMS_PATH = ROOT / "data" / "site-claims.json"
SCHEMA_SNAPSHOT = ROOT / "data" / "beawar-schema-original.json"
MAP_SNAPSHOT = ROOT / "data" / "beawar-map-original.json"
CANONICAL_HOST = "https://www.superpest.in"
REVIEW_SCRIPT = re.compile(
    r"""[ \t]*<script\b(?=[^>]*\bsrc=["']/js/location-reviews\.js(?:\?[^"']*)?["'])[^>]*>\s*</script>[ \t]*\r?\n?""",
    re.I,
)
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
}


class Node:
    def __init__(self, tag: str, attrs: dict[str, str | None] | None = None):
        self.tag = tag
        self.attrs = attrs or {}
        self.children: list[Node | str] = []


class TreeParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, dict(attrs)))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def plain_text(node: Node) -> str:
    pieces: list[str] = []

    def visit(item: Node | str):
        if isinstance(item, str):
            pieces.append(item)
        else:
            if item.tag in {"br", "p", "div", "li"}:
                pieces.append(" ")
            for child in item.children:
                visit(child)
            if item.tag in {"p", "div", "li"}:
                pieces.append(" ")

    visit(node)
    return re.sub(r"\s+", " ", html.unescape(" ".join(pieces))).strip()


def descendants(node: Node, tag: str | None = None):
    for child in node.children:
        if isinstance(child, Node):
            if tag is None or child.tag == tag:
                yield child
            yield from descendants(child, tag)


def faq_pairs(document: str) -> dict[str, str]:
    parser = TreeParser()
    parser.feed(document)
    pairs: dict[str, str] = {}
    for node in descendants(parser.root):
        classes = set((node.attrs.get("class") or "").split())
        if node.tag == "details":
            question_nodes = list(descendants(node, "summary"))
            answer_nodes = list(descendants(node, "p"))
        elif node.tag in {"article", "div"} and "area-faq" in classes:
            question_nodes = [
                child for child in descendants(node)
                if child.tag in {"h3", "summary"}
            ][:1]
            answer_nodes = list(descendants(node, "p"))
        else:
            continue
        if question_nodes and answer_nodes:
            question = plain_text(question_nodes[0]).casefold()
            answer = plain_text(answer_nodes[0])
            if question and answer:
                pairs[question] = answer
    return pairs


def is_faq_page(value) -> bool:
    types = value.get("@type", []) if isinstance(value, dict) else []
    if isinstance(types, str):
        types = [types]
    return "FAQPage" in types


def sync_faq_nodes(value, visible: dict[str, str]) -> tuple[object, bool]:
    changed = False
    if isinstance(value, list):
        result = []
        for item in value:
            updated, item_changed = sync_faq_nodes(item, visible)
            changed |= item_changed
            if updated is not None:
                result.append(updated)
        return result, changed
    if not isinstance(value, dict):
        return value, False

    if is_faq_page(value):
        questions = value.get("mainEntity", [])
        kept = []
        for question in questions if isinstance(questions, list) else []:
            if not isinstance(question, dict):
                changed = True
                continue
            key = re.sub(
                r"\s+",
                " ",
                html.unescape(str(question.get("name", ""))),
            ).strip().casefold()
            answer = visible.get(key)
            if not answer:
                changed = True
                continue
            accepted = question.get("acceptedAnswer")
            if not isinstance(accepted, dict):
                accepted = {"@type": "Answer"}
                changed = True
            if accepted.get("text") != answer:
                accepted["text"] = answer
                changed = True
            question["acceptedAnswer"] = accepted
            kept.append(question)
        if value.get("mainEntity") != kept:
            value["mainEntity"] = kept
            changed = True

    for key, item in list(value.items()):
        updated, item_changed = sync_faq_nodes(item, visible)
        if updated is None:
            del value[key]
            changed = True
        elif item_changed:
            value[key] = updated
            changed = True
    return value, changed


def remove_schema_types(value) -> tuple[object, bool]:
    changed = False
    if isinstance(value, list):
        result = []
        for item in value:
            updated, item_changed = remove_schema_types(item)
            changed |= item_changed
            if updated is not None:
                result.append(updated)
        return result, changed
    if not isinstance(value, dict):
        return value, False
    schema_type = value.get("@type", [])
    types = {schema_type} if isinstance(schema_type, str) else set(schema_type or [])
    if types & {"Review", "AggregateRating"}:
        return None, True
    for key, item in list(value.items()):
        updated, item_changed = remove_schema_types(item)
        if updated is None:
            del value[key]
            changed = True
        elif item_changed:
            value[key] = updated
            changed = True
    return value, changed


def mentions_beawar(value) -> bool:
    if isinstance(value, dict):
        return any(mentions_beawar(k) or mentions_beawar(v) for k, v in value.items())
    if isinstance(value, list):
        return any(mentions_beawar(item) for item in value)
    return isinstance(value, str) and "beawar" in value.casefold()


def hold_beawar_schema(value) -> tuple[object, bool]:
    changed = False
    if isinstance(value, list):
        result = []
        for item in value:
            updated, item_changed = hold_beawar_schema(item)
            changed |= item_changed
            if updated is not None:
                result.append(updated)
        return result, changed
    if not isinstance(value, dict):
        return value, False

    for key, item in list(value.items()):
        key_lower = key.casefold()
        if key_lower == "sameas":
            values = item if isinstance(item, list) else [item]
            kept = [entry for entry in values if not mentions_beawar(entry)]
            if kept != values:
                value[key] = kept if isinstance(item, list) else (kept[0] if kept else None)
                changed = True
            if value.get(key) is None:
                del value[key]
            continue
        if key_lower in {"address", "geo", "hasmap", "office", "location"} and mentions_beawar(item):
            del value[key]
            changed = True
            continue
        if key_lower == "areaserved":
            values = item if isinstance(item, list) else [item]
            kept = [entry for entry in values if not mentions_beawar(entry)]
            if kept != values:
                value[key] = kept if isinstance(item, list) else (kept[0] if kept else None)
                changed = True
            if value.get(key) is None:
                del value[key]
            continue
        updated, item_changed = hold_beawar_schema(item)
        if updated is None:
            del value[key]
            changed = True
        elif item_changed:
            value[key] = updated
            changed = True
    return value, changed


def replace_jsonld(document: str, *, hold_beawar: bool) -> tuple[str, int, int]:
    faq_changes = 0
    hold_changes = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal faq_changes, hold_changes
        source = match.group(2)
        try:
            value = json.loads(source.replace("<\\/", "</"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON-LD block: {error}") from error
        value, review_changed = remove_schema_types(value)
        if review_changed:
            faq_changes += 1
        visible = faq_pairs(document)
        value, faq_changed = sync_faq_nodes(value, visible)
        if faq_changed:
            faq_changes += 1
        if hold_beawar:
            value, beawar_changed = hold_beawar_schema(value)
            if beawar_changed:
                hold_changes += 1
        encoded = json.dumps(value, ensure_ascii=False, indent=2)
        return f"{match.group(1)}\n{encoded}\n{match.group(3)}"

    updated = re.sub(
        r'(<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>)(.*?)(</script>)',
        replace,
        document,
        flags=re.I | re.S,
    )
    return updated, faq_changes, hold_changes


def map_elements(document: str) -> list[re.Match[str]]:
    map_url = re.compile(r"(?:google\.[^/]+/maps|maps\.app\.goo\.gl|g\.page/)", re.I)
    pattern = re.compile(
        r"<a\b[^>]*>.*?</a\s*>|<iframe\b[^>]*>.*?</iframe\s*>",
        re.I | re.S,
    )
    return [
        match for match in pattern.finditer(document)
        if map_url.search(match.group())
        and "beawar" in match.group().casefold()
    ]


def remove_map_references(document: str) -> tuple[str, int]:
    elements = map_elements(document)
    for index, match in reversed(list(enumerate(elements))):
        marker = f"<!--SPS-MAP-HOLD-{index}-->"
        document = document[:match.start()] + marker + document[match.end():]
    return document, len(elements)


def restore_map_references(document: str, fragments: list[str]) -> str:
    for index, fragment in enumerate(fragments):
        document = document.replace(f"<!--SPS-MAP-HOLD-{index}-->", fragment, 1)
    return document


def apply_review_policy(document: str, claims: dict, relative_path: str) -> tuple[str, int]:
    verified = claims.get("reviewsVerified", False)
    if verified is True:
        if relative_path.startswith("pest-control-in-") and "/index.html" in relative_path:
            if not REVIEW_SCRIPT.search(document):
                document = re.sub(
                    r"</body\s*>",
                    '    <script src="/js/location-reviews.js?v=20261014" defer></script>\n</body>',
                    document,
                    count=1,
                    flags=re.I,
                )
                return document, 1
        return document, 0
    document, removed = REVIEW_SCRIPT.subn("", document)
    if verified != "some":
        return document, removed

    list_path = ROOT / "data" / "verified-reviews.json"
    approved = json.loads(list_path.read_text(encoding="utf-8")) if list_path.exists() else []
    if not isinstance(approved, list):
        raise ValueError("data/verified-reviews.json must contain a JSON array")
    if relative_path != "index.html":
        document, cards_removed = re.subn(
            r"<article\b[^>]*class=[\"'][^\"']*\breview-card\b[^\"']*[\"'][^>]*>.*?</article\s*>",
            "",
            document,
            flags=re.I | re.S,
        )
        document = re.sub(
            r"<section\b[^>]*class=[\"'][^\"']*\breviews-preview\b[^\"']*[\"'][^>]*>.*?</section\s*>",
            "",
            document,
            flags=re.I | re.S,
        )
        return document, removed + cards_removed

    approved_by_key = {
        (
            re.sub(r"\s+", " ", str(item.get("name", ""))).strip().casefold(),
            re.sub(r"\s+", " ", str(item.get("text", ""))).strip().casefold(),
        ): item
        for item in approved
        if isinstance(item, dict)
    }
    cards = []
    for key, entry in approved_by_key.items():
        date_value = str(entry.get("date", "")).strip()
        source_value = str(entry.get("source", "")).strip()
        name_value = str(entry.get("name", "")).strip()
        text_value = str(entry.get("text", "")).strip()
        if not name_value or not text_value or not date_value or not source_value:
            raise ValueError("Every verified review needs name, text, date, and source")
        cards.append(
            '<article class="review-card">'
            f'<p>{html.escape(text_value)}</p>'
            f'<strong>{html.escape(name_value)}</strong>'
            f'<small class="review-source">Verified {html.escape(date_value)} · '
            f'Source: {html.escape(source_value)}</small>'
            '</article>'
        )

    card_pattern = re.compile(
        r"<article\b[^>]*class=[\"'][^\"']*\breview-card\b[^\"']*[\"'][^>]*>.*?</article\s*>",
        re.I | re.S,
    )
    matches = list(card_pattern.finditer(document))
    if cards and not matches:
        raise ValueError("Verified reviews cannot be placed because the homepage has no review-card container")
    if matches:
        first = matches[0]
        marker = "<!--SPS-VERIFIED-REVIEWS-->"
        document = (
            document[:first.start()]
            + marker
            + document[first.end():]
        )
        document, removed_cards = card_pattern.subn("", document)
        document = document.replace(marker, "\n".join(cards), 1)
        removed += removed_cards
    if not cards:
        document = re.sub(
            r"<section\b[^>]*class=[\"'][^\"']*\breviews-preview\b[^\"']*[\"'][^>]*>.*?</section\s*>",
            "",
            document,
            flags=re.I | re.S,
        )
    return document, removed


def rewrite_images(document: str) -> tuple[str, int]:
    images = list(re.finditer(r"<img\b[^>]*>", document, re.I))
    if not images:
        return document, 0
    hero_index = None
    for index, match in enumerate(images):
        prefix = document[max(0, match.start() - 220):match.start()].casefold()
        tag = match.group().casefold()
        in_header = prefix.rfind("<header") > prefix.rfind("</header")
        is_logo = in_header or "logo" in tag or "logo" in prefix[-100:]
        width = re.search(r'\bwidth=["\']?(\d+)', tag)
        is_large = bool(width and int(width.group(1)) >= 600) or "srcset=" in tag
        if not is_logo and is_large:
            hero_index = index
            break
    if hero_index is None:
        for index, match in enumerate(images):
            prefix = document[max(0, match.start() - 220):match.start()].casefold()
            tag = match.group().casefold()
            if prefix.rfind("<header") <= prefix.rfind("</header") and "logo" not in tag:
                hero_index = index
                break

    changes = 0

    def set_attribute(tag: str, name: str, value: str) -> tuple[str, int]:
        attribute = re.search(
            rf'\b{name}\s*=\s*(["\'])(.*?)\1',
            tag,
            re.I | re.S,
        )
        if attribute:
            if attribute.group(2).casefold() == value:
                return tag, 0
            return (
                tag[:attribute.start()]
                + f'{name}="{value}"'
                + tag[attribute.end():],
                1,
            )
        closing = "/>" if tag.rstrip().endswith("/>") else ">"
        return tag[:-len(closing)] + f' {name}="{value}"' + closing, 1

    for index in range(len(images) - 1, -1, -1):
        match = images[index]
        tag = match.group()
        prefix = document[max(0, match.start() - 220):match.start()].casefold()
        in_header = prefix.rfind("<header") > prefix.rfind("</header")
        is_logo = in_header or "logo" in tag.casefold() or "logo" in prefix[-100:]
        if is_logo:
            continue
        if index == hero_index:
            tag, changed = set_attribute(tag, "fetchpriority", "high")
            changes += changed
            tag, changed = set_attribute(tag, "loading", "eager")
            changes += changed
        else:
            tag, changed = set_attribute(tag, "loading", "lazy")
            changes += changed
            tag, changed = set_attribute(tag, "decoding", "async")
            changes += changed
        document = document[:match.start()] + tag + document[match.end():]
    return document, changes


def add_main_landmark(document: str) -> tuple[str, bool]:
    if re.search(r"<main\b", document, re.I):
        return document, False
    header = re.search(r"</header\s*>", document, re.I)
    footer = re.search(r"<footer\b", document, re.I)
    if not header or not footer or header.end() >= footer.start():
        raise ValueError("Cannot safely place main landmark around existing page content")
    document = (
        document[:header.end()]
        + "\n<main>\n"
        + document[header.end():footer.start()]
        + "\n</main>\n"
        + document[footer.start():]
    )
    return document, True


def update_location_hub(document: str) -> tuple[str, bool]:
    if "locations-directory-links" in document:
        return document, False
    grid = re.search(r'<div\b[^>]*class=["\'][^"\']*\blocations-grid\b[^"\']*["\'][^>]*>', document, re.I)
    if not grid:
        return document, False
    tag_pattern = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)
    depth = 1
    grid_close = None
    for tag in tag_pattern.finditer(document, grid.end()):
        if tag.group().lower().startswith("</"):
            depth -= 1
            if depth == 0:
                grid_close = tag.start()
                break
        else:
            depth += 1
    if grid_close is None:
        raise ValueError("Could not locate the service-area card directory")
    cards_fragment = document[grid.end():grid_close]
    cards = []
    for anchor in re.finditer(r'<a\b([^>]*\bclass=["\'][^"\']*\blocation-card\b[^"\']*["\'][^>]*)>(.*?)</a\s*>', cards_fragment, re.I | re.S):
        href = re.search(r'\bhref=["\']([^"\']+)["\']', anchor.group(1), re.I)
        if not href:
            continue
        text = re.search(r"<(?:h[2-4]|strong|span)\b[^>]*>(.*?)</(?:h[2-4]|strong|span)\s*>", anchor.group(2), re.I | re.S)
        label = re.sub(r"<[^>]+>", " ", text.group(1) if text else "", flags=re.S)
        label = re.sub(r"\s+", " ", html.unescape(label)).strip()
        if not label:
            slug = href.group(1).rstrip("/").split("/")[-1].removeprefix("pest-control-in-")
            label = slug.replace("_", " ").replace("-", " ").title()
        cards.append(f'<li><a href="{html.escape(href.group(1), quote=True)}">Pest control services in {html.escape(label)}</a></li>')
    if not cards:
        raise ValueError("The service-location district list could not be derived from its existing cards")
    directory = (
        '<section class="locations-directory-links" aria-labelledby="district-directory-heading">'
        '<h2 id="district-directory-heading">Browse pest control by district</h2>'
        '<p>Choose a district to view its service areas and the locations covered. Contact the team to confirm availability for a specific address.</p>'
        '<ul>' + "\n".join(cards) + "</ul></section>\n"
    )
    intro = (
        '<p class="locations-introduction">This directory links to the district pages and their listed areas. '
        'Review nearby coverage and contact the team to confirm service availability for your property.</p>\n'
    )
    document = document[:grid.start()] + intro + directory + document[grid.start():]
    return document, True


def update_contact_page(document: str) -> tuple[str, bool]:
    if "contact-enquiry-process" in document:
        return document, False
    insertion = re.search(r'(<div\b[^>]*class=["\'][^"\']*\bcontact-info\b[^"\']*["\'][^>]*>.*?</p>)', document, re.I | re.S)
    if not insertion:
        return document, False
    section = """
            <section class="contact-enquiry-process" aria-labelledby="enquiry-process-heading">
                <h3 id="enquiry-process-heading">What happens after an enquiry</h3>
                <p>We use the details you provide to follow up about the service you requested. Enquiries can be made for locations across Rajasthan; contact us to confirm availability for your area.</p>
                <p>Call <a href="tel:+919828066990">+91 98280 66990</a> or <a href="tel:+917976572984">+91 79765 72984</a>, or message us on <a href="https://wa.me/917976572984" target="_blank" rel="noopener noreferrer">WhatsApp</a>.</p>
            </section>
"""
    document = document[:insertion.end()] + section + document[insertion.end():]
    return document, True


def remove_unapproved_certification_claims(document: str, has_approved_wording: bool) -> tuple[str, int]:
    if has_approved_wording:
        return document, 0
    removals = 0

    starts = [
        match for match in re.finditer(r"<div\b[^>]*>", document, re.I)
        if re.search(
            r'\bclass=["\'][^"\']*\b(?:location-card|check-item|feature-item)\b',
            match.group(),
            re.I,
        )
    ]
    div_tokens = re.compile(r"<div\b[^>]*>|</div\s*>", re.I)
    for start in reversed(starts):
        depth = 1
        end = None
        for token in div_tokens.finditer(document, start.end()):
            depth += -1 if token.group().lower().startswith("</") else 1
            if depth == 0:
                end = token.end()
                break
        if end is None:
            raise ValueError("Unclosed location card while removing unapproved credentials")
        card = document[start.start():end]
        content = plain_text_from_fragment(card).casefold()
        is_location_card = "location-card" in start.group().casefold()
        is_self_claim = re.search(
            r"\b(?:we are|we have|our technicians|our team|active members|the business holds|"
            r"we proudly|fully certified|certified & recognized)\b",
            content,
        )
        if ("niphm" in content or "ipca" in content) and (is_location_card or is_self_claim):
            document = document[:start.start()] + document[end:]
            removals += 1

    def remove_paragraph(match: re.Match[str]) -> str:
        nonlocal removals
        text = plain_text_from_fragment(match.group())
        if "niphm" in text.casefold() and (
            "trained" in text.casefold()
            or "certif" in text.casefold()
            or "ipca" in text.casefold()
        ):
            removals += 1
            return ""
        if "ipca" in text.casefold() and (
            "member" in text.casefold() or "certif" in text.casefold()
        ):
            removals += 1
            return ""
        if "certified in audit-compliant pest management programmes" in text.casefold():
            removals += 1
            return ""
        return match.group()

    document = re.sub(r"<p\b[^>]*>.*?</p\s*>", remove_paragraph, document, flags=re.I | re.S)
    document, credential_cards = re.subn(
        r"<div\b[^>]*>\s*<strong>\s*(?:CERTIFICATION|PROFESSIONAL TRAINING|INDUSTRY MEMBERSHIP)\s*</strong>.*?</div\s*>",
        "",
        document,
        count=0,
        flags=re.I | re.S,
    )
    removals += credential_cards
    document = re.sub(
        r'(\balt=["\'])[^"\']*(?:NIPHM|training certificate)[^"\']*(["\'])',
        r'\1Pest management training event\2',
        document,
        flags=re.I,
    )
    return document, removals


def apply_experience_policy(
    document: str, claims: dict, relative_path: str
) -> tuple[str, int]:
    wording = claims.get("experienceWording")
    approved = (
        wording.strip()
        if isinstance(wording, str)
        and wording.strip()
        and not wording.strip().startswith("[[TO-FILL")
        else ""
    )
    time_claim = re.compile(
        r"\b(?:\d{2,3}\s+years?|three\s+decades|two\s+and\s+a\s+half\s+decades|decades|"
        r"since\s+(?:19|20)\d{2})\b",
        re.I,
    )
    changed = 0
    stat = re.compile(
        r"<div\b[^>]*>\s*<strong>\s*(?:28|30)\s+years?\s*</strong>\s*"
        r"<span>\s*Experience\s*</span>\s*</div>",
        re.I | re.S,
    )

    def replace_stat(match: re.Match[str]) -> str:
        nonlocal changed
        replacement = (
            f"<div><strong>{html.escape(approved)}</strong></div>"
            if approved
            else ""
        )
        if replacement != match.group():
            changed += 1
        return replacement

    document = stat.sub(replace_stat, document)

    if relative_path == "about/index.html":
        story = re.compile(
            r"(<p\b[^>]*>\s*<b>\s*Our Story\s*</b>).*?(</p\s*>)",
            re.I | re.S,
        )
        def replace_story(match: re.Match[str]) -> str:
            nonlocal changed
            suffix = f" {html.escape(approved)}." if approved else ""
            replacement = (
                match.group(1)
                + " Super Pest Control Services provides pest management for residential "
                + "and commercial customers across Rajasthan."
                + suffix
                + match.group(2)
            )
            if replacement != match.group():
                changed += 1
            return replacement

        document = story.sub(replace_story, document, count=1)

    def update_paragraph(match: re.Match[str]) -> str:
        nonlocal changed
        opening, content, closing = match.groups()
        visible = plain_text_from_fragment(content)
        if relative_path == "about/index.html" and visible.casefold().startswith("our story"):
            return match.group()
        if not time_claim.search(visible):
            return match.group()
        if "pests don't rest" in visible.casefold():
            content = re.sub(
                r"Pests\s+don['’]t\s+rest,\s*and\s+for\s+\d+\s+years?,\s*neither\s+have\s+we\.?",
                "",
                content,
                flags=re.I,
            )
            content = re.sub(
                r"Proven techniques,\s*uncompromising safety standards,\s*and\s*"
                r"(?:three decades|\d+\s+years?)[^.!?]*[.!?]?",
                "",
                content,
                flags=re.I,
            )
            content = (html.escape(approved) + ". " if approved else "") + content
        else:
            content = html.escape(approved) if approved else ""
        replacement = opening + content + closing
        if replacement != match.group():
            changed += 1
        return replacement

    document = re.sub(
        r"(<p\b[^>]*>)(.*?)(</p\s*>)",
        update_paragraph,
        document,
        flags=re.I | re.S,
    )
    return document, changed


def plain_text_from_fragment(fragment: str) -> str:
    parser = TreeParser()
    parser.feed(fragment)
    return plain_text(parser.root)


def apply() -> dict[str, int]:
    claims = json.loads(CLAIMS_PATH.read_text(encoding="utf-8"))
    hold_beawar = claims.get("HOLD_BEAWAR", True) is True
    has_approved_certification = bool(
        isinstance(claims.get("certificationWording"), str)
        and claims["certificationWording"].strip()
        and not claims["certificationWording"].startswith("[[TO-FILL")
        and claims["certificationWording"].strip().casefold() != "none to state"
    )
    html_files = sorted(ROOT.rglob("*.html"))
    jsonld_pattern = re.compile(
        r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script\s*>',
        re.I | re.S,
    )
    for path in html_files:
        content = path.read_text(encoding="utf-8", errors="replace")
        for match in jsonld_pattern.finditer(content):
            try:
                json.loads(match.group(1).replace("<\\/", "</"))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON-LD in {path.relative_to(ROOT).as_posix()}: {error}"
                ) from error
    changed_pages = 0
    removed_review_includes = 0
    faq_blocks_changed = 0
    beawar_schema_changes = 0
    image_attr_changes = 0
    main_added = 0
    map_references_removed = 0
    host_rewrites = 0
    sitemap_host_rewrites = 0
    review_schema_pages_removed = 0
    unapproved_certification_blocks_removed = 0
    experience_claims_replaced = 0

    if hold_beawar and not SCHEMA_SNAPSHOT.exists():
        originals = {}
        for path in html_files:
            content = path.read_text(encoding="utf-8", errors="replace")
            schemas = re.findall(
                r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>',
                content, re.I | re.S
            )
            if any("beawar" in block.casefold() for block in schemas):
                originals[path.relative_to(ROOT).as_posix()] = schemas
        SCHEMA_SNAPSHOT.write_text(json.dumps(originals, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif not hold_beawar and SCHEMA_SNAPSHOT.exists():
        originals = json.loads(SCHEMA_SNAPSHOT.read_text(encoding="utf-8"))
        rel_to_files = {p.relative_to(ROOT).as_posix(): p for p in html_files}
        for rel, schemas in originals.items():
            path = rel_to_files.get(rel)
            if path is None:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            matches = list(re.finditer(
                r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>',
                content, re.I | re.S
            ))
            if len(matches) != len(schemas):
                raise ValueError(f"Schema changed unexpectedly; cannot restore Beawar schema safely: {rel}")
            for match, schema in reversed(list(zip(matches, schemas))):
                content = content[:match.start()] + schema + content[match.end():]
            path.write_text(content, encoding="utf-8", newline="\n")

    if hold_beawar and not MAP_SNAPSHOT.exists():
        originals = {}
        for path in html_files:
            relative = path.relative_to(ROOT).as_posix()
            content = path.read_text(encoding="utf-8", errors="replace")
            matches = map_elements(content)
            if matches:
                originals[relative] = [match.group() for match in matches]
        MAP_SNAPSHOT.write_text(
            json.dumps(originals, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    elif not hold_beawar and MAP_SNAPSHOT.exists():
        originals = json.loads(MAP_SNAPSHOT.read_text(encoding="utf-8"))
        rel_to_files = {p.relative_to(ROOT).as_posix(): p for p in html_files}
        for rel, fragments in originals.items():
            path = rel_to_files.get(rel)
            if path is None:
                continue
            content = path.read_text(encoding="utf-8", errors="replace")
            restored = restore_map_references(content, fragments)
            if restored != content:
                path.write_text(restored, encoding="utf-8", newline="\n")

    for path in html_files:
        before = path.read_text(encoding="utf-8", errors="replace")
        document = before
        document, experience_count = apply_experience_policy(
            document, claims, path.relative_to(ROOT).as_posix()
        )
        experience_claims_replaced += experience_count
        if re.search(r'"@type"\s*:\s*"(?:Review|AggregateRating)"', document):
            review_schema_pages_removed += 1
        document, certification_count = remove_unapproved_certification_claims(
            document, has_approved_certification
        )
        unapproved_certification_blocks_removed += certification_count
        document, removed = apply_review_policy(
            document, claims, path.relative_to(ROOT).as_posix()
        )
        removed_review_includes += removed
        document, host_count = re.subn(r"https://superpest\.in", CANONICAL_HOST, document, flags=re.I)
        host_rewrites += host_count

        original_schema_count = len(re.findall(
            r'<script\b[^>]*type=["\']application/ld\+json["\'][^>]*>.*?</script>',
            document, re.I | re.S
        ))
        document, faq_count, held_count = replace_jsonld(document, hold_beawar=hold_beawar)
        faq_blocks_changed += faq_count
        beawar_schema_changes += held_count
        map_count = 0
        if hold_beawar:
            document, map_count = remove_map_references(
                document
            )
        map_references_removed += map_count

        if path.relative_to(ROOT).as_posix() in {
            "about/index.html",
            "contact/index.html",
            "commercial-pest-control/index.html",
            "residential-pest-control/index.html",
        }:
            document, added = add_main_landmark(document)
            main_added += int(added)
        if path.relative_to(ROOT).as_posix() == "service-location/index.html":
            document, _ = update_location_hub(document)
        if path.relative_to(ROOT).as_posix() == "contact/index.html":
            document, _ = update_contact_page(document)
        if path.relative_to(ROOT).as_posix() == "blog/index.html":
            def fix_whatsapp(match: re.Match[str]) -> str:
                tag = match.group()
                if not re.search(r'\bclass=["\'][^"\']*\bwhatsapp\b', tag, re.I):
                    return tag
                tag = re.sub(r'\bhref=["\']#["\']', 'href="https://wa.me/917976572984"', tag, flags=re.I)
                if not re.search(r'\btarget\s*=', tag, re.I):
                    tag = tag[:-1] + ' target="_blank">'
                if not re.search(r'\brel\s*=', tag, re.I):
                    tag = tag[:-1] + ' rel="noopener noreferrer">'
                return tag

            document = re.sub(r"<a\b[^>]*>", fix_whatsapp, document, flags=re.I)

        rel = path.relative_to(ROOT).as_posix()
        overlap_file = ROOT / "data" / "overlap-flagged-pages.json"
        flagged_pages = (
            set(json.loads(overlap_file.read_text(encoding="utf-8")))
            if overlap_file.exists()
            else set()
        )
        if rel in flagged_pages:
            document, _ = re.subn(
                r'<section\b(?=[^>]*aria-labelledby=["\']why-choose-us-heading["\'])[^>]*>.*?</section\s*>',
                "",
                document,
                count=1,
                flags=re.I | re.S,
            )

        document, image_count = rewrite_images(document)
        image_attr_changes += image_count
        if document != before:
            path.write_text(document, encoding="utf-8", newline="\n")
            changed_pages += 1

    sitemap = ROOT / "sitemap.xml"
    if sitemap.exists():
        sitemap_text = sitemap.read_text(encoding="utf-8")
        sitemap_text, sitemap_host_rewrites = re.subn(
            r"https://superpest\.in",
            CANONICAL_HOST,
            sitemap_text,
            flags=re.I,
        )
        if sitemap_host_rewrites:
            sitemap.write_text(sitemap_text, encoding="utf-8", newline="\n")

    return {
        "html_files_scanned": len(html_files),
        "html_pages_changed": changed_pages,
        "location_review_includes_removed": removed_review_includes,
        "faq_schema_updates": faq_blocks_changed,
        "Beawar_schema_nodes_removed": beawar_schema_changes,
        "Beawar_maps_removed": map_references_removed,
        "canonical_host_rewrites": host_rewrites,
        "sitemap_host_rewrites": sitemap_host_rewrites,
        "image_attribute_updates": image_attr_changes,
        "main_landmarks_added": main_added,
        "review_schema_removed": review_schema_pages_removed,
        "unapproved_certification_blocks_removed": unapproved_certification_blocks_removed,
        "experience_claims_replaced": experience_claims_replaced,
    }


if __name__ == "__main__":
    for key, value in apply().items():
        print(f"{key}: {value}")
