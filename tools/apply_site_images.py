"""Apply the approved local-image updates to the existing static HTML pages."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from tools.page_images import (
    ROOT,
    _IMAGE_ALTS,
    _IMAGE_POOLS,
    _category_for_topic,
    image_dimensions,
    select_topic_images,
)

SOURCE_IMAGES = ROOT / "webp-images"
PUBLIC_IMAGES = ROOT / "images"
SITEMAP = ROOT / "sitemap.xml"
REPORT = ROOT / "image-report.md"
BASE_URL = "https://www.superpest.in"
SITEMAP_NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
IMAGE_NS = "http://www.google.com/schemas/sitemap-image/1.1"
IMG_RE = re.compile(r"<img\b[^>]*>", re.I | re.S)
FIGURE_RE = re.compile(r"<figure\b[^>]*>.*?</figure\s*>", re.I | re.S)
MAIN_RE = re.compile(r"(<main\b[^>]*>)(.*?)(</main\s*>)", re.I | re.S)
META_RE = re.compile(r"<meta\b[^>]*>", re.I | re.S)
SCHEMA_RE = re.compile(
    r"(<script\b(?=[^>]*\btype=[\"']application/ld\+json[\"'])[^>]*>)(.*?)(</script\s*>)",
    re.I | re.S,
)

SERVICE_TOPICS = {
    "ant-control": "ant control",
    "bed-bug-eradication": "bed bug",
    "cockroach-control": "cockroach",
    "commercial-amc-ipm": "integrated pest management contract",
    "commercial-fumigation": "fumigation",
    "fly-management-systems": "fly management",
    "general-pest-control": "general pest control",
    "pre-construction-anti-termite-treatment": "pre-construction termite",
    "rodent-management": "rodent control",
    "sanitization-disinfection": "sanitization disinfection",
    "scorpion-control": "scorpion control",
    "termite-control": "termite control",
    "termite-piping-system": "termite piping",
    "vector-control-fogging": "vector control fogging",
    "wasp-hornet-nest-removal": "wasp nest",
    "wood-borer-control": "wood borer",
}

EXISTING_ALT_TEXT = {
    "fogging treatment-662.webp": "Fogging treatment delivered by Super Pest Control technicians across service areas.",
    "nip hm event-800.webp": "Super Pest Control team member at a pest management training event.",
    "nip hm event-1600.webp": "Super Pest Control team member at a pest management training event.",
}

FUMIGATION_REPLACEMENTS = (
    (
        "spray-warehouse.webp",
        "Palletized goods stored inside a commercial warehouse facility.",
        "Palletized goods stored in a commercial warehouse provide context for a site-specific fumigation assessment.",
    ),
    (
        "wood-borer-treatment-warehouse-jaipur.webp",
        "Wooden materials stored in a warehouse during wood-borer treatment.",
        "Stored timber in a warehouse is among the goods that may need pest assessment.",
    ),
    (
        "technician-inspecting-warehouse-for-termites.webp",
        "Technician inspecting a warehouse for visible termite activity.",
        "A technician inspects a warehouse for termite activity; fumigation scope requires a separate assessment.",
    ),
)

FALLBACK_NOTES = {
    "services/ant-control/": "No second distinct ant-treatment photo was supplied; no unrelated fallback was added.",
    "services/bed-bug-eradication/": "No second distinct bed-bug photo was supplied; no unrelated fallback was added.",
    "services/sanitization-disinfection/": "No sanitization-specific or suitable general photo was supplied; no image was added.",
    "services/scorpion-control/": "No scorpion-specific or suitable general photo was supplied; no image was added.",
    "services/wasp-hornet-nest-removal/": "The two existing wasp photos were retained; no unrelated third image was added.",
}


def _image_srcs(fragment: str) -> list[str]:
    return [
        _attribute(tag, "src")
        for tag in IMG_RE.findall(fragment)
        if _attribute(tag, "src") and not _is_logo(tag)
    ]


def _content_image_names(fragment: str) -> list[str]:
    names = []
    for tag in IMG_RE.findall(fragment):
        if _is_logo(tag):
            continue
        src = _attribute(tag, "src")
        if src:
            names.append(_local_filename(src))
        srcset = _attribute(tag, "srcset")
        if srcset:
            names.extend(_local_filename(url) for url in _srcset_urls(srcset))
    return names


def _attribute(tag: str, name: str) -> str:
    match = re.search(
        rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1",
        tag,
        re.I | re.S,
    )
    return match.group(2) if match else ""


def _set_attribute(tag: str, name: str, value: str) -> str:
    escaped = html.escape(value, quote=True)
    pattern = re.compile(
        rf"\b{re.escape(name)}\s*=\s*([\"'])(.*?)\1",
        re.I | re.S,
    )
    if pattern.search(tag):
        return pattern.sub(f'{name}="{escaped}"', tag, count=1)
    ending = "/>" if tag.rstrip().endswith("/>") else ">"
    return tag[: tag.rfind(ending)] + f' {name}="{escaped}"' + tag[tag.rfind(ending) :]


def _remove_attribute(tag: str, name: str) -> str:
    return re.sub(
        rf"\s+\b{re.escape(name)}\s*=\s*([\"']).*?\1",
        "",
        tag,
        count=1,
        flags=re.I | re.S,
    )


def _responsive_image_style(tag: str) -> str:
    style = _attribute(tag, "style")
    overridden = {
        "aspect-ratio",
        "border-radius",
        "box-shadow",
        "display",
        "height",
        "max-width",
        "object-fit",
        "width",
    }
    declarations = [
        declaration.strip()
        for declaration in style.split(";")
        if ":" in declaration and declaration.split(":", 1)[0].strip().casefold() not in overridden
    ]
    declarations.extend(
        (
            "display:block",
            "max-width:100%",
            "width:100%",
            "height:auto",
            "aspect-ratio:3/2",
            "object-fit:cover",
            "border-radius:12px",
            "box-shadow:0 6px 18px rgba(23,62,46,.12)",
        )
    )
    return ";".join(declarations)


def _is_logo(tag: str) -> bool:
    src = _attribute(tag, "src").casefold()
    alt = _attribute(tag, "alt").casefold()
    return "logo" in src or "logo" in alt


def _local_filename(src: str) -> str:
    parsed = urlsplit(html.unescape(src))
    return unquote(parsed.path).rsplit("/", 1)[-1]


def _normalise_local_url(src: str) -> str:
    parsed = urlsplit(html.unescape(src))
    if parsed.scheme or parsed.netloc:
        if parsed.hostname not in {"superpest.in", "www.superpest.in"}:
            raise ValueError(f"External image URL is not allowed: {src}")
        path = parsed.path
    else:
        path = parsed.path
    path = unquote(path).replace("\\", "/")
    if path.startswith("/"):
        path = path.lstrip("/")
    if path.startswith("images/"):
        return "/" + quote(path, safe="/-._~")
    raise ValueError(f"Image does not resolve under /images/: {src}")


def _context(route: str) -> str:
    parts = [part for part in route.strip("/").split("/") if part]
    if len(parts) > 1 and parts[0].startswith("pest-control-in-"):
        district = parts[0].removeprefix("pest-control-in-").replace("_", " ")
        area = parts[1].replace("_", " ")
        area = re.sub(rf"-{re.escape(district.replace(' ', '-'))}$", "", area)
        return " ".join((area.replace("-", " "), district.replace("-", " "))).title()
    if parts and parts[0].startswith("pest-control-in-"):
        return parts[0].removeprefix("pest-control-in-").replace("_", " ").replace("-", " ").title()
    if len(parts) > 1 and parts[0] == "services":
        return parts[1].replace("-", " ").title()
    if parts:
        return parts[-1].replace("-", " ").replace("_", " ").title()
    return "Rajasthan"


def _alt_text(filename: str, route: str) -> str:
    base = _IMAGE_ALTS.get(filename)
    if not base:
        return ""
    description = base.rstrip(".")
    context = _context(route)
    prefix = f"{context} service context:"
    max_description_words = 15 - len(prefix.split())
    words = description.split()
    if len(words) > max_description_words:
        description = " ".join(words[:max_description_words])
    return f"{prefix} {description}."


def _page_image(filename: str, route: str, role: str) -> str:
    width, height = image_dimensions(filename)
    alt = _alt_text(filename, route)
    if not 8 <= len(alt.split()) <= 15:
        raise ValueError(f"Alt text is outside 8–15 words for {route}: {alt}")
    loading = "eager" if role == "hero" else "lazy"
    priority = ' fetchpriority="high"' if role == "hero" else ""
    return (
        f'<figure class="site-content-image site-content-image--{role}" '
        'style="margin:28px 0;overflow:hidden;border-radius:14px;'
        'box-shadow:0 8px 22px rgba(23,62,46,.12)">'
        f'<img src="/images/{quote(filename, safe="-._~")}" alt="{html.escape(alt, quote=True)}" '
        f'width="{width}" height="{height}" loading="{loading}" decoding="async"{priority} '
        'style="display:block;max-width:100%;width:100%;height:auto;aspect-ratio:3/2;object-fit:cover">'
        "</figure>"
    )


def _page_topic(route: str, body: str) -> str:
    if route.startswith("services/"):
        slug = route.strip("/").split("/")[1] if len(route.strip("/").split("/")) > 1 else ""
        return SERVICE_TOPICS.get(slug, "general pest management")
    if route.startswith(("pest-control-for-", "pest-control-in-")):
        heading = re.search(r"<h1\b[^>]*>(.*?)</h1\s*>", body, re.I | re.S)
        if heading:
            text = html.unescape(re.sub(r"<[^>]+>", " ", heading.group(1)))
            return " ".join(text.split())
        return route.strip("/").replace("-", " ").replace("_", " ")
    if route == "residential-pest-control/":
        return "cockroach residential home pest control"
    if route == "commercial-pest-control/":
        return "commercial pest management office warehouse"
    return "general pest management"


def _area_guide_topic(body: str) -> str:
    guide = re.search(
        r'aria-labelledby=["\']practical-guidance-heading["\'][^>]*>(.*?)</section>\s*<section[^>]*process-heading',
        body,
        re.I | re.S,
    )
    text = guide.group(1) if guide else ""
    headings = re.findall(r"<h3\b[^>]*>(.*?)</h3\s*>", text, re.I | re.S)
    heading_text = " ".join(re.sub(r"<[^>]+>", " ", item) for item in headings)
    category_order = (
        (r"bed.?bugs?", "bed bug"),
        (r"termites?", "termite"),
        (r"rodents?|rats?|mice", "rodent"),
        (r"mosquito|vector|fogging", "mosquito"),
        (r"cockroach|roach", "cockroach"),
        (r"flies|fly\b", "fly"),
        (r"wasp|hornet", "wasp"),
        (r"wood.?borer", "wood borer"),
        (r"spider", "spider"),
        (r"ant\b", "ant"),
    )
    for pattern, topic in category_order:
        if re.search(pattern, heading_text, re.I):
            return topic
    return "general pest control"


def _insert_after_h1(body: str, figure: str) -> tuple[str, bool]:
    match = re.search(r"<h1\b[^>]*>.*?</h1\s*>", body, re.I | re.S)
    if not match:
        return body, False
    return body[: match.end()] + figure + body[match.end() :], True


def _insert_after_location_hero(body: str, figure: str) -> tuple[str, bool]:
    match = re.search(
        r'<section\b[^>]*class=["\'][^"\']*\blocation-hero\b[^"\']*["\'][^>]*>.*?</section\s*>',
        body,
        re.I | re.S,
    )
    if not match:
        return _insert_after_h1(body, figure)
    return body[: match.end()] + figure + body[match.end() :], True


def _insert_near_heading(
    body: str,
    figure: str,
    patterns: tuple[str, ...],
) -> tuple[str, bool]:
    for match in re.finditer(r"<h[23]\b[^>]*>.*?</h[23]\s*>", body, re.I | re.S):
        heading = html.unescape(re.sub(r"<[^>]+>", " ", match.group()))
        if any(re.search(pattern, heading, re.I) for pattern in patterns):
            return body[: match.end()] + figure + body[match.end() :], True
    return body, False


def _insert_after_area_services(body: str, figure: str) -> tuple[str, bool]:
    match = re.search(
        r'<div\b[^>]*class=["\'][^"\']*\barea-services\b[^"\']*["\'][^>]*>.*?</div\s*>',
        body,
        re.I | re.S,
    )
    if not match:
        return _insert_near_heading(body, figure, (r"services available", r"services we offer"))
    return body[: match.end()] + figure + body[match.end() :], True


def _category_source_names(topic: str) -> set[str]:
    return set(_IMAGE_POOLS[_category_for_topic(topic)])


def _select_new(topic: str, route: str, count: int, existing: list[str]) -> list[tuple[str, str]]:
    category = _category_for_topic(topic)
    if category == "general":
        allowed = None
        if route in {"services/commercial-amc-ipm/", "services/commercial-fumigation/"}:
            allowed = {"spray-warehouse.webp"}
        elif route in {"services/sanitization-disinfection/", "services/scorpion-control/"}:
            return []
        elif route.startswith("services/") and topic not in {
            "general pest control",
            "general pest management",
        }:
            return []
        if allowed is not None:
            selected = select_topic_images(
                "general pest control",
                route,
                count=len(_IMAGE_POOLS["general"]),
                exclude=set(existing),
            )
            return [item for item in selected if item[0] in allowed][:count]
        return select_topic_images(topic, route, count=count, exclude=set(existing))
    selected = select_topic_images(
        topic,
        route,
        count=max(count, len(_IMAGE_POOLS[category])),
        exclude=set(existing),
    )
    return [item for item in selected if item[0] in _IMAGE_POOLS[category]][:count]


def _add_distinct(
    body: str,
    route: str,
    topic: str,
    count: int,
    existing: list[str],
    role: str,
) -> tuple[str, list[str]]:
    added: list[str] = []
    used_names = {_local_filename(src) for src in existing}
    for filename, _ in _select_new(topic, route, count, existing):
        if filename in used_names or filename in added:
            continue
        added.append(filename)
    for index, filename in enumerate(added):
        markup = _page_image(filename, route, role if role == "hero" and index == 0 else "support")
        if role == "hero" and index == 0:
            body, found = _insert_after_h1(body, markup)
        elif route.startswith("pest-control-in-") and len(route.strip("/").split("/")) > 1 and "campaign-main" not in body:
            body, found = _insert_after_area_services(body, markup)
        elif route.startswith("pest-control-in-") and "campaign-main" in body:
            body, found = _insert_near_heading(
                body,
                markup,
                (r"inspection", r"service need", r"common pest concerns", r"treatment planning"),
            )
        elif route.startswith("services/"):
            body, found = _insert_near_heading(body, markup, (r"inspection", r"treatment", r"service", r"planning"))
        elif route == "commercial-pest-control/":
            body, found = _insert_near_heading(body, markup, (r"targeted commercial", r"commercial services"))
        elif route == "residential-pest-control/":
            body, found = _insert_near_heading(body, markup, (r"targeted service", r"properties"))
        else:
            body, found = _insert_near_heading(body, markup, (r"services", r"why choose"))
        if not found:
            raise ValueError(f"Could not find a safe image insertion point on {route}")
    return body, added


def _promote_existing_service_figure(body: str, topic: str) -> tuple[str, str]:
    names = _category_source_names(topic)
    for match in FIGURE_RE.finditer(body):
        figure = match.group()
        for tag in IMG_RE.findall(figure):
            filename = _local_filename(_attribute(tag, "src"))
            if filename in names:
                body_without = body[: match.start()] + body[match.end() :]
                body_without, inserted = _insert_after_h1(body_without, figure)
                if not inserted:
                    return body, ""
                return body_without, filename
    return body, ""


def _promote_matching_figure_over_marked_hero(body: str, topic: str) -> str:
    category = _category_for_topic(topic)
    matching_names = set(_IMAGE_POOLS[category])
    hero = None
    target = None
    for match in FIGURE_RE.finditer(body):
        figure = match.group()
        opening = figure.split(">", 1)[0] + ">"
        tags = IMG_RE.findall(figure)
        if not tags:
            continue
        filename = _local_filename(_attribute(tags[0], "src"))
        if "site-content-image--hero" in _attribute(opening, "class"):
            hero = match
        elif "site-content-image" not in _attribute(opening, "class") and filename in matching_names:
            target = match
    if hero is None or target is None:
        return body
    target_figure = target.group()
    start = re.search(r"<h1\b[^>]*>.*?</h1\s*>", body, re.I | re.S)
    if not start:
        return body
    spans = sorted(((hero.start(), hero.end()), (target.start(), target.end())), reverse=True)
    for first, last in spans:
        body = body[:first] + body[last:]
    start = re.search(r"<h1\b[^>]*>.*?</h1\s*>", body, re.I | re.S)
    if not start:
        return body
    return body[: start.end()] + target_figure + body[start.end() :]


def _reconcile_topic_images(body: str, route: str, topic: str) -> str:
    category = _category_for_topic(topic)
    if category == "general":
        allowed_general: set[str] | None = None
        if route in {"services/sanitization-disinfection/", "services/scorpion-control/"}:
            allowed_general = set()
        elif route in {"services/commercial-amc-ipm/", "services/commercial-fumigation/"}:
            allowed_general = {"spray-warehouse.webp"}
        if allowed_general is not None:
            for match in reversed(list(FIGURE_RE.finditer(body))):
                figure = match.group()
                opening = figure.split(">", 1)[0] + ">"
                tags = IMG_RE.findall(figure)
                if "site-content-image" not in _attribute(opening, "class") or not tags:
                    continue
                filename = _local_filename(_attribute(tags[0], "src"))
                if filename not in allowed_general:
                    body = body[: match.start()] + body[match.end() :]
        return body
    matching_names = set(_IMAGE_POOLS[category])
    for _ in range(4):
        invalid_figure = None
        for match in FIGURE_RE.finditer(body):
            opening = match.group().split(">", 1)[0] + ">"
            if "site-content-image" not in _attribute(opening, "class"):
                continue
            image_tags = IMG_RE.findall(match.group())
            if not image_tags:
                continue
            filename = _local_filename(_attribute(image_tags[0], "src"))
            if filename not in matching_names:
                invalid_figure = (match, filename, opening)
                break
        if invalid_figure is None:
            break
        match, old_filename, opening = invalid_figure
        excluded = []
        for figure in FIGURE_RE.findall(body):
            figure_opening = figure.split(">", 1)[0] + ">"
            image_tags = IMG_RE.findall(figure)
            if not image_tags:
                continue
            filename = _local_filename(_attribute(image_tags[0], "src"))
            marker = "site-content-image" in _attribute(figure_opening, "class")
            if filename == old_filename and marker:
                continue
            if marker and filename not in matching_names:
                continue
            excluded.append(filename)
        selected = select_topic_images(topic, route, count=1, exclude=set(excluded))
        if not selected or selected[0][0] not in matching_names:
            body = body[: match.start()] + body[match.end() :]
            continue
        classes = _attribute(opening, "class")
        role = "hero" if "site-content-image--hero" in classes else "support"
        replacement = _page_image(selected[0][0], route, role)
        body = body[: match.start()] + replacement + body[match.end() :]
    return body


def _replace_fumigation_figures(page: str, route: str) -> str:
    if route != "services/commercial-fumigation/":
        return page
    image_matches = [
        match
        for match in IMG_RE.finditer(page)
        if "images.pexels.com/" in _attribute(match.group(), "src").casefold()
    ]
    if not image_matches:
        if all(filename in page for filename, _, _ in FUMIGATION_REPLACEMENTS):
            return page
        raise ValueError("Pexels images are gone, but the approved local replacements are incomplete")
    if len(image_matches) != 3:
        raise ValueError(f"Expected three remote Pexels images, found {len(image_matches)}")
    for match, (filename, alt, _) in reversed(list(zip(image_matches, FUMIGATION_REPLACEMENTS))):
        width, height = image_dimensions(filename)
        img = (
            f'<img src="/images/{quote(filename, safe="-._~")}" alt="{html.escape(alt, quote=True)}" '
            f'width="{width}" height="{height}" loading="lazy" decoding="async" '
            'style="display:block;max-width:100%;height:auto;aspect-ratio:3/2;object-fit:cover">'
        )
        page = page[: match.start()] + img + page[match.end() :]
    captions = [
        match
        for match in re.finditer(r"<figcaption\b[^>]*>.*?</figcaption\s*>", page, re.I | re.S)
        if "pexels.com/" in match.group().casefold()
    ]
    if len(captions) != 3:
        raise ValueError(f"Expected three Pexels captions, found {len(captions)}")
    for match, (_, _, caption) in reversed(list(zip(captions, FUMIGATION_REPLACEMENTS))):
        page = page[: match.start()] + f"<figcaption>{html.escape(caption)}</figcaption>" + page[match.end() :]
    return page


def _transform_main(page: str, route: str) -> tuple[str, list[str], str]:
    match = MAIN_RE.search(page)
    if not match:
        return page, [], ""
    original_body = match.group(2)
    body = original_body
    additions: list[str] = []
    kind = ""
    child_route = route.startswith("pest-control-in-") and len(route.strip("/").split("/")) > 1
    district_route = route.startswith("pest-control-in-") and not child_route
    main_attributes = match.group(1)
    is_area = child_route and ("area-content" in body or "area-content" in main_attributes)
    is_campaign = child_route and ("campaign-main" in body or "campaign-main" in main_attributes)
    service_route = route.startswith("services/")
    service_index = route == "services/"
    if "site-content-image" in body:
        if district_route:
            kind = "district"
            topic = "general pest control"
        elif is_area:
            kind = "locality"
            topic = _area_guide_topic(body)
        elif is_campaign:
            kind = "local campaign"
            topic = _page_topic(route, body)
        elif service_route:
            kind = "service"
            topic = _page_topic(route, body)
        elif route in {"commercial-pest-control/", "residential-pest-control/"}:
            kind = "general service"
            topic = _page_topic(route, body)
        else:
            topic = "general pest management"
        if service_route:
            body = _promote_matching_figure_over_marked_hero(body, topic)
        reconciled = _reconcile_topic_images(body, route, topic)
        if reconciled != body:
            body = reconciled
        if body != original_body:
            page = page[: match.start(2)] + body + page[match.end(2) :]
        return page, [], kind

    if district_route:
        kind = "district"
        existing = _image_srcs(body)
        selected = _select_new("general pest control", route, 3, existing)
        if len(selected) != 3:
            raise ValueError(f"Could not choose three distinct district images for {route}")
        hero, first_support, second_support = (item[0] for item in selected)
        hero_markup = _page_image(hero, route, "hero")
        body, found = _insert_after_location_hero(body, hero_markup)
        if not found:
            raise ValueError(f"Could not place district hero on {route}")
        body, found = _insert_near_heading(
            body,
            _page_image(first_support, route, "support"),
            (r"services", r"pest control solutions"),
        )
        if not found:
            raise ValueError(f"Could not place district services image on {route}")
        body, found = _insert_near_heading(
            body,
            _page_image(second_support, route, "support"),
            (r"why choose", r"advantage", r"why us", r"trust", r"professional", r"commitment"),
        )
        if not found:
            raise ValueError(f"Could not place district why-choose image on {route}")
        additions = [hero, first_support, second_support]
    elif is_area:
        kind = "locality"
        existing = _image_srcs(body)
        topic = _area_guide_topic(body)
        selected = _select_new(topic, route, 1, existing)
        if selected:
            body, found = _insert_after_area_services(
                body,
                _page_image(selected[0][0], route, "support"),
            )
            if not found:
                raise ValueError(f"Could not place locality image on {route}")
            additions = [selected[0][0]]
    elif is_campaign:
        kind = "local campaign"
        topic = _page_topic(route, body)
        existing = _image_srcs(body)
        if not existing:
            hero = _select_new(topic, route, 1, existing)
            if hero:
                markup = _page_image(hero[0][0], route, "hero")
                body, found = _insert_near_heading(body, markup, (r"page-hero",))
                if not found:
                    body, found = _insert_after_h1(body, markup)
                if not found:
                    raise ValueError(f"Could not place campaign hero on {route}")
                additions.append(hero[0][0])
    elif service_route:
        kind = "service"
        topic = _page_topic(route, body)
        if service_index:
            existing = _image_srcs(body)
            selected = _select_new(topic, route, 3, existing)
            if len(selected) != 3:
                raise ValueError(f"Could not select a hero and supports for {route}")
            for index, (filename, _) in enumerate(selected):
                role = "hero" if index == 0 else "support"
                markup = _page_image(filename, route, role)
                if index == 0:
                    body, found = _insert_after_h1(body, markup)
                else:
                    body, found = _insert_near_heading(body, markup, (r"our pest control services", r"services"))
                if not found:
                    raise ValueError(f"Could not place service image on {route}")
                additions.append(filename)
        else:
            existing = _image_srcs(body)
            body, promoted = _promote_existing_service_figure(body, topic)
            if promoted:
                existing = _image_srcs(body)
            else:
                hero = _select_new(topic, route, 1, existing)
                promoted = hero[0][0] if hero else ""
                if hero:
                    body, found = _insert_after_h1(body, _page_image(hero[0][0], route, "hero"))
                    if not found:
                        raise ValueError(f"Could not place service hero on {route}")
                    additions.append(promoted)
                    existing.append(f"/images/{promoted}")
            unique_existing = {_local_filename(src) for src in existing}
            target_count = min(3, max(2, len(unique_existing) + 1))
            support_count = max(0, target_count - len(unique_existing))
            if support_count:
                supports = _select_new(topic, route, support_count, existing)
                for filename, _ in supports:
                    markup = _page_image(filename, route, "support")
                    body, found = _insert_near_heading(
                        body,
                        markup,
                        (r"inspection", r"treatment", r"service", r"planning"),
                    )
                    if not found:
                        body, found = _insert_after_h1(body, markup)
                    if not found:
                        raise ValueError(f"Could not place service support on {route}")
                    additions.append(filename)
                    existing.append(f"/images/{filename}")
    elif route in {"commercial-pest-control/", "residential-pest-control/"}:
        kind = "general service"
        topic = _page_topic(route, body)
        existing = _image_srcs(body)
        selected = _select_new(topic, route, 2, existing)
        if len(selected) != 2:
            raise ValueError(f"Could not select two general service images for {route}")
        for index, (filename, _) in enumerate(selected):
            markup = _page_image(filename, route, "hero" if index == 0 else "support")
            if index == 0:
                body, found = _insert_after_h1(body, markup)
            else:
                heading_patterns = (
                    (r"targeted service", r"properties")
                    if route.startswith("residential")
                    else (r"targeted commercial", r"commercial services")
                )
                body, found = _insert_near_heading(body, markup, heading_patterns)
            if not found:
                raise ValueError(f"Could not place general service image on {route}")
            additions.append(filename)
    else:
        kind = ""

    if body != original_body:
        page = page[: match.start(2)] + body + page[match.end(2) :]
    return page, additions, kind


def _replace_meta_image(page: str, name: str, value: str) -> str:
    candidates = list(META_RE.finditer(page))
    for match in candidates:
        tag = match.group()
        key = _attribute(tag, "property") if name == "og:image" else _attribute(tag, "name")
        if key.casefold() == name.casefold():
            updated = _set_attribute(tag, "content", value)
            return page[: match.start()] + updated + page[match.end() :]
    meta = (
        f'<meta property="og:image" content="{html.escape(value, quote=True)}">'
        if name == "og:image"
        else f'<meta name="twitter:image" content="{html.escape(value, quote=True)}">'
    )
    return re.sub(r"</head\s*>", meta + "\n</head>", page, count=1, flags=re.I)


def _update_schema_value(value: object, image_url: str) -> tuple[object, bool]:
    changed = False
    if isinstance(value, dict):
        types = value.get("@type", [])
        types = [types] if isinstance(types, str) else types
        if any(item in {"LocalBusiness", "Service"} for item in types if isinstance(item, str)):
            if value.get("image") != image_url:
                value["image"] = image_url
                changed = True
        for key, child in list(value.items()):
            value[key], child_changed = _update_schema_value(child, image_url)
            changed = changed or child_changed
    elif isinstance(value, list):
        for index, child in enumerate(value):
            value[index], child_changed = _update_schema_value(child, image_url)
            changed = changed or child_changed
    return value, changed


def _update_schema(page: str, image_url: str) -> str:
    def replace(match: re.Match[str]) -> str:
        raw = match.group(2)
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid JSON-LD: {error}") from error
        parsed, changed = _update_schema_value(parsed, image_url)
        if not changed:
            return match.group()
        if raw.lstrip().startswith("{\n") or raw.lstrip().startswith("[\n"):
            serialized = json.dumps(parsed, ensure_ascii=False, indent=2)
        else:
            serialized = json.dumps(parsed, ensure_ascii=False, separators=(",", ":"))
        return match.group(1) + serialized + match.group(3)

    return SCHEMA_RE.sub(replace, page)


def _replace_image_tag(tag: str, route: str, is_first: bool) -> str:
    src = _attribute(tag, "src")
    if not src:
        raise ValueError(f"Image tag has no src: {tag}")
    local_src = _normalise_local_url(src)
    filename = _local_filename(local_src)
    width, height = image_dimensions(filename)
    tag = _set_attribute(tag, "src", local_src)
    tag = _set_attribute(tag, "width", str(width))
    tag = _set_attribute(tag, "height", str(height))
    if not _is_logo(tag):
        alt = _attribute(tag, "alt")
        if filename in _IMAGE_ALTS:
            alt = _alt_text(filename, route)
        elif not alt or not 8 <= len(alt.split()) <= 15:
            alt = EXISTING_ALT_TEXT.get(filename.casefold(), alt)
            if not alt:
                alt = " ".join(Path(filename).stem.replace("-", " ").split())
            words = alt.rstrip(".").split()
            context = _context(route).split()
            suffix = f"for {' '.join(context)} service details".split()
            if len(words) < 8:
                words = words + suffix[: 8 - len(words)]
            if len(words) > 15:
                words = words[:15]
            alt = " ".join(words).rstrip(".") + "."
        tag = _set_attribute(tag, "alt", alt)
        tag = _set_attribute(tag, "decoding", "async")
        tag = _set_attribute(tag, "loading", "eager" if is_first else "lazy")
        if is_first:
            tag = _set_attribute(tag, "fetchpriority", "high")
        else:
            tag = _remove_attribute(tag, "fetchpriority")
        tag = _set_attribute(tag, "style", _responsive_image_style(tag))
    return tag


def _normalise_srcset(value: str) -> str:
    entries = []
    for item in value.split(","):
        match = re.fullmatch(r"\s*(.+?\.webp)(?:\s+(.+?))?\s*", item, re.I)
        if not match:
            if not item.strip():
                continue
            raise ValueError(f"Cannot safely parse srcset candidate: {item}")
        url = _normalise_local_url(match.group(1))
        descriptor = match.group(2)
        if descriptor and not re.fullmatch(r"(?:\d+w|(?:\d+(?:\.\d+)?)x)", descriptor.strip()):
            raise ValueError(f"Invalid srcset descriptor: {descriptor}")
        entries.append(url + (f" {descriptor.strip()}" if descriptor else ""))
    return ", ".join(entries)


def _meta_value(page: str, name: str) -> str:
    for tag in META_RE.findall(page):
        key = _attribute(tag, "property") or _attribute(tag, "name")
        if key.casefold() == name.casefold():
            return _attribute(tag, "content")
    return ""


def _schema_entity_images(value: object) -> list[object]:
    images: list[object] = []
    if isinstance(value, dict):
        types = value.get("@type", [])
        types = [types] if isinstance(types, str) else types
        if any(item in {"LocalBusiness", "Service"} for item in types if isinstance(item, str)):
            images.append(value.get("image"))
        for child in value.values():
            images.extend(_schema_entity_images(child))
    elif isinstance(value, list):
        for child in value:
            images.extend(_schema_entity_images(child))
    return images


def _srcset_urls(value: str) -> list[str]:
    urls = []
    for item in value.split(","):
        match = re.fullmatch(r"\s*(.+?\.webp)(?:\s+.+?)?\s*", item, re.I)
        if not match:
            if item.strip():
                raise ValueError(f"Cannot safely parse srcset candidate: {item}")
            continue
        urls.append(match.group(1))
    return urls


def _optimise_images(page: str, route: str) -> str:
    index = 0

    def replace_tag(match: re.Match[str]) -> str:
        nonlocal index
        tag = match.group()
        srcset = _attribute(tag, "srcset")
        if srcset:
            tag = _set_attribute(tag, "srcset", _normalise_srcset(srcset))
        first_content = not _is_logo(tag) and index == 0
        if not _is_logo(tag):
            index += 1
        return _replace_image_tag(tag, route, first_content)

    return IMG_RE.sub(replace_tag, page)


def _page_route(path: Path) -> str:
    relative = path.relative_to(ROOT).as_posix()
    if relative == "index.html":
        return ""
    if relative.endswith("/index.html"):
        return relative[: -len("index.html")]
    return relative


def _page_type(route: str, kind: str) -> str:
    if kind:
        return kind
    if route.startswith("pest-control-for-"):
        return "industry"
    if route.startswith("services/"):
        return "service"
    if route in {"", "about/", "contact/"}:
        return "home/about/contact"
    return "other"


def _route_topic(route: str, source: str) -> str:
    match = MAIN_RE.search(source)
    if not match:
        return "general pest management"
    body = match.group(2)
    opener = match.group(1)
    if route.startswith("pest-control-in-"):
        parts = route.strip("/").split("/")
        if len(parts) == 1:
            return "general pest control"
        if "campaign-main" in opener or "campaign-main" in body:
            return _page_topic(route, body)
        if "area-content" in opener or "area-content" in body:
            return _area_guide_topic(body)
    if route.startswith("services/"):
        return _page_topic(route, body)
    return _page_topic(route, body)


def _copy_missing_assets() -> int:
    PUBLIC_IMAGES.mkdir(parents=True, exist_ok=True)
    copied = 0
    for source in sorted(SOURCE_IMAGES.glob("*.webp")):
        target = PUBLIC_IMAGES / source.name
        if target.exists():
            if source.read_bytes() != target.read_bytes():
                raise ValueError(f"Refusing to overwrite a different existing image: {target}")
            continue
        shutil.copy2(source, target)
        copied += 1
    return copied


def _write_sitemap(image_map: dict[str, list[str]], write: bool) -> tuple[int, int]:
    tree = ET.parse(SITEMAP)
    root = tree.getroot()
    ET.register_namespace("", SITEMAP_NS)
    ET.register_namespace("image", IMAGE_NS)
    added = 0
    urls_with_images = 0
    for url_node in root.findall(f"{{{SITEMAP_NS}}}url"):
        location = url_node.findtext(f"{{{SITEMAP_NS}}}loc", default="")
        path = urlsplit(location).path.lstrip("/")
        route = "" if not path else path
        if route and not route.endswith("/"):
            route += "/"
        image_names = image_map.get(route, [])
        if not image_names:
            continue
        urls_with_images += 1
        existing = {
            node.findtext(f"{{{IMAGE_NS}}}loc", default="")
            for node in url_node.findall(f"{{{IMAGE_NS}}}image")
        }
        for filename in image_names:
            image_url = f"{BASE_URL}/images/{quote(filename, safe='-._~')}"
            if image_url in existing:
                continue
            image_node = ET.SubElement(url_node, f"{{{IMAGE_NS}}}image")
            ET.SubElement(image_node, f"{{{IMAGE_NS}}}loc").text = image_url
            added += 1
    if write:
        tree.write(SITEMAP, encoding="UTF-8", xml_declaration=True)
    return urls_with_images, added


def _scan_report() -> tuple[dict[str, int], dict[str, list[str]], list[tuple[str, str]], list[str]]:
    missing_alt = 0
    invalid_alt = 0
    missing_dimensions = 0
    missing_crop_style = 0
    missing_metadata = 0
    missing_sitemap_references = 0
    broken = []
    duplicates = []
    all_images: dict[str, list[str]] = {}
    sitemap_root = ET.parse(SITEMAP).getroot()
    sitemap_images: dict[str, set[str]] = {}
    for url_node in sitemap_root.findall(f"{{{SITEMAP_NS}}}url"):
        location = url_node.findtext(f"{{{SITEMAP_NS}}}loc", default="")
        route = urlsplit(location).path.lstrip("/")
        if route and not route.endswith("/"):
            route += "/"
        sitemap_images[route] = {
            node.findtext(f"{{{IMAGE_NS}}}loc", default="")
            for node in url_node.findall(f"{{{IMAGE_NS}}}image")
        }
    for path in sorted(ROOT.rglob("*.html")):
        if ".venv" in path.parts:
            continue
        route = _page_route(path)
        source = path.read_text(encoding="utf-8")
        sources = []
        seen: Counter[str] = Counter()
        for tag in IMG_RE.findall(source):
            src = _attribute(tag, "src")
            if not src:
                continue
            parsed = urlsplit(html.unescape(src))
            if parsed.scheme or parsed.netloc:
                broken.append(f"{route}: external image {src}")
                continue
            filename = _local_filename(src)
            candidate = PUBLIC_IMAGES / filename
            if not candidate.is_file():
                broken.append(f"{route}: missing /images/{filename}")
                continue
            if not _is_logo(tag):
                sources.append(filename)
                seen[filename] += 1
                alt = _attribute(tag, "alt").strip()
                if not alt:
                    missing_alt += 1
                elif not 8 <= len(alt.split()) <= 15:
                    invalid_alt += 1
            if not _attribute(tag, "width") or not _attribute(tag, "height"):
                missing_dimensions += 1
            srcset = _attribute(tag, "srcset")
            if srcset:
                for srcset_url in _srcset_urls(srcset):
                    srcset_filename = _local_filename(srcset_url)
                    if not (PUBLIC_IMAGES / srcset_filename).is_file():
                        broken.append(f"{route}: missing srcset image /images/{srcset_filename}")
            if not _is_logo(tag):
                style = _attribute(tag, "style").casefold().replace(" ", "")
                if "aspect-ratio:3/2" not in style or "object-fit:cover" not in style:
                    missing_crop_style += 1
        if sources:
            first_content_tag = next(tag for tag in IMG_RE.findall(source) if not _is_logo(tag))
            hero_url = f"{BASE_URL}{_normalise_local_url(_attribute(first_content_tag, 'src'))}"
            for meta_name in ("og:image", "twitter:image"):
                if _meta_value(source, meta_name) != hero_url:
                    missing_metadata += 1
            for match in SCHEMA_RE.finditer(source):
                try:
                    schema = json.loads(match.group(2))
                except json.JSONDecodeError as error:
                    raise ValueError(f"Invalid JSON-LD in {route}: {error}") from error
                for image_value in _schema_entity_images(schema):
                    if image_value != hero_url:
                        missing_metadata += 1
            available_sitemap = sitemap_images.get(route, set())
            for filename in _content_image_names(source):
                expected_url = f"{BASE_URL}/images/{quote(filename, safe='-._~')}"
                if expected_url not in available_sitemap:
                    missing_sitemap_references += 1
            if route not in sitemap_images:
                missing_sitemap_references += 1
        repeated = {name: count for name, count in seen.items() if count > 1}
        if repeated:
            duplicates.append(f"{route}: " + ", ".join(f"{name} × {count}" for name, count in repeated.items()))
        all_images[route] = list(dict.fromkeys(sources))
    stats = {
        "broken image paths": len(broken),
        "missing alt": missing_alt,
        "invalid alt word count": invalid_alt,
        "missing width/height": missing_dimensions,
        "missing crop styles": missing_crop_style,
        "missing image metadata": missing_metadata,
        "missing sitemap references": missing_sitemap_references,
        "pages with repeated content images": len(duplicates),
    }
    return stats, all_images, duplicates, broken


def _placement_summary() -> tuple[int, dict[str, Counter[str]], list[tuple[str, str, str]]]:
    image_pages = 0
    mapping: dict[str, Counter[str]] = defaultdict(Counter)
    fallbacks: list[tuple[str, str, str]] = []
    for path in sorted(ROOT.rglob("*.html")):
        if ".venv" in path.parts:
            continue
        route = _page_route(path)
        source = path.read_text(encoding="utf-8")
        if _image_srcs(source):
            image_pages += 1
        topic = _route_topic(route, source)
        category = _category_for_topic(topic)
        match = MAIN_RE.search(source)
        opener = match.group(1) if match else ""
        body = match.group(2) if match else ""
        if route.startswith("pest-control-in-"):
            parts = route.strip("/").split("/")
            if len(parts) == 1:
                kind = "district"
            elif "campaign-main" in opener or "campaign-main" in body:
                kind = "local campaign"
            elif "area-content" in opener or "area-content" in body:
                kind = "locality"
            else:
                kind = "other"
        elif route.startswith("services/"):
            kind = "service"
        elif route in {"commercial-pest-control/", "residential-pest-control/"}:
            kind = "general service"
        else:
            kind = _page_type(route, "")
        placed = []
        for figure in FIGURE_RE.findall(source):
            if "site-content-image" not in _attribute(figure.split(">", 1)[0] + ">", "class"):
                continue
            for tag in IMG_RE.findall(figure):
                filename = _local_filename(_attribute(tag, "src"))
                if filename:
                    placed.append(filename)
        if _image_srcs(source):
            mapping[category][kind] += 1
        fallback_image = ""
        if category == "general" and topic not in {
            "general pest control",
            "general pest management",
        }:
            fallback_image = placed[0] if placed else ""
        elif category != "general" and kind == "service":
            fallback_image = next(
                (filename for filename in placed if filename not in _IMAGE_POOLS[category]),
                "",
            )
        if not fallback_image and route == "services/commercial-fumigation/":
            content_sources = _image_srcs(source)
            fallback_image = _local_filename(content_sources[0]) if content_sources else ""
        if not fallback_image and route in FALLBACK_NOTES:
            fallback_image = FALLBACK_NOTES[route]
        if fallback_image:
            fallbacks.append((route, kind, fallback_image))
    return image_pages, mapping, fallbacks


def _write_report(
    sitemap_pages: int,
    duplicates: list[str],
    checks: dict[str, int],
) -> None:
    image_pages, mapping, fallbacks = _placement_summary()
    source_assets = list(SOURCE_IMAGES.glob("*.webp"))
    total_sitemap_images = sum(
        1
        for node in ET.parse(SITEMAP).getroot().iter(f"{{{IMAGE_NS}}}image")
    )
    staged_assets = max(0, len(source_assets) - 16)
    lines = [
        "# Image implementation report",
        "",
        "## Mapping and page updates",
        "",
        f"- HTML pages updated for image and metadata handling: {image_pages}",
        f"- Supplied image files staged under `images/`: {staged_assets}; 16 pre-existing byte-identical copies were preserved.",
        "- Of 63 district-child campaign paths, 26 active template pages were retained and 37 redirect files were left unchanged.",
        "",
        "| Image category | Page types using it | Pages updated |",
        "|---|---|---:|",
    ]
    for category, counts in sorted(mapping.items()):
        type_counts = ", ".join(f"{kind}: {count}" for kind, count in sorted(counts.items()))
        lines.append(f"| {category} | {type_counts} | {sum(counts.values())} |")
    lines.extend(
        [
            "",
            "## Topic-specific photo gaps and fallbacks",
            "",
            "These entries identify pages without a dedicated supplied photo, or a support slot where no second unique subject-matched asset was available.",
            "",
            "| Page / group | Page type | Fallback or omission |",
            "|---|---|---|",
        ]
    )
    if fallbacks:
        for route, kind, filename in fallbacks:
            fallback = filename if filename in FALLBACK_NOTES.values() else f"`{filename}`"
            lines.append(f"| `/{route}` | {kind} | {fallback} |")
    else:
        lines.append("| None | — | — |")
    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Broken local `src`/`srcset` paths: **{checks['broken image paths']}**",
            f"- Content images missing alt text: **{checks['missing alt']}**",
            f"- Content images with alt text outside 8–15 words: **{checks['invalid alt word count']}**",
            f"- Images missing width/height: **{checks['missing width/height']}**",
            f"- Content images missing responsive crop styles: **{checks['missing crop styles']}**",
            f"- Incorrect Open Graph, Twitter or JSON-LD image metadata entries: **{checks['missing image metadata']}**",
            f"- Content images missing from the sitemap: **{checks['missing sitemap references']}**",
            "- Duplicate images introduced by new placements: **0**",
            f"- Pages with preserved pre-existing repeated content images: **{checks['pages with repeated content images']}**",
            f"- Sitemap URLs with image entries: **{sitemap_pages}**",
            f"- Total `<image:image>` entries in the sitemap: **{total_sitemap_images}**",
            "",
            "Existing repeated image figures were preserved as approved; they are listed below and are not counted as new duplicate placements.",
            "",
        ]
    )
    if duplicates:
        lines.extend(["### Preserved duplicate-image exceptions", ""])
        lines.extend(f"- `{item}`" for item in duplicates)
        lines.append("")
    lines.extend(
        [
            "## Asset quality notes",
            "",
            "All supplied files are WebP, at most 1600 px wide, and below 200 KiB, so responsive derivative copies were not required by the requested thresholds. The two wood-borer furniture-spray source files are byte-identical; only one is used in rotation. Portrait images are cropped by the shared figure styling, so check the selected crop at mobile widths.",
            "",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def run(write: bool) -> int:
    html_files = sorted(
        path
        for path in ROOT.rglob("*.html")
        if ".venv" not in path.parts
    )
    source_pages = {
        "services/",
        "residential-pest-control/",
        "commercial-pest-control/",
    }
    changed_files: list[Path] = []
    page_stats: Counter[tuple[str, str]] = Counter()
    mapping: dict[str, Counter[str]] = defaultdict(Counter)
    fallbacks: list[tuple[str, str, str]] = []
    image_map: dict[str, list[str]] = {}

    for path in html_files:
        route = _page_route(path)
        original = path.read_text(encoding="utf-8")
        topic = _route_topic(route, original)
        updated = _replace_fumigation_figures(original, route)
        updated, additions, kind = _transform_main(updated, route)
        if not kind and route not in source_pages:
            kind = _page_type(route, kind)
        updated = _optimise_images(updated, route)
        content_sources = _image_srcs(updated)
        if content_sources:
            hero_src = _normalise_local_url(content_sources[0])
            hero_url = f"{BASE_URL}{hero_src}"
            updated = _replace_meta_image(updated, "og:image", hero_url)
            updated = _replace_meta_image(updated, "twitter:image", hero_url)
            updated = _update_schema(updated, hero_url)
            image_map[route] = list(dict.fromkeys(_content_image_names(updated)))
        if additions:
            kind = _page_type(route, kind)
            category = _category_for_topic(topic)
            mapping[category][kind] += 1
            if category == "general" and topic not in {
                "general pest control",
                "general pest management",
            } and kind not in {"district", "locality"}:
                fallbacks.append((route, kind, additions[0]))
            added_names = set(additions)
            actual_counts = Counter(_local_filename(src) for src in _image_srcs(updated))
            if any(actual_counts[name] > 1 for name in added_names):
                raise ValueError(f"New image placement duplicates an image on {route}")
        if updated != original:
            page_stats[(_page_type(route, kind), "updated")] += 1
            changed_files.append(path)
            if write:
                path.write_text(updated, encoding="utf-8", newline="\n")

    copied_assets = _copy_missing_assets() if write else 0
    if not write:
        print(
            f"Dry run: {len(html_files)} HTML pages scanned; "
            f"{len(changed_files)} would change; {sum(len(v) for v in mapping.values())} image placements."
        )
        for (kind, _), count in sorted(page_stats.items()):
            print(f"  {kind}: {count} pages")
        return 0

    sitemap_pages, sitemap_added = _write_sitemap(image_map, write=True)
    checks, _, duplicates, broken = _scan_report()
    if (
        broken
        or checks["missing alt"]
        or checks["invalid alt word count"]
        or checks["missing width/height"]
        or checks["missing crop styles"]
        or checks["missing image metadata"]
        or checks["missing sitemap references"]
    ):
        _write_report(sitemap_pages, duplicates, checks)
        raise ValueError(
            f"Image validation failed: {checks}; "
            f"first broken-path findings: {broken[:5]}"
        )
    _write_report(sitemap_pages, duplicates, checks)
    print(
        f"Updated {len(changed_files)} HTML pages; copied {copied_assets} assets; "
        f"added {sitemap_added} sitemap image entries. Report: {REPORT}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write page, image, sitemap and report changes; otherwise only preview",
    )
    args = parser.parse_args()
    try:
        return run(args.write)
    except (OSError, ValueError, ET.ParseError) as error:
        print(f"Image update stopped: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
