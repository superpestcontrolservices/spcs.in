"""Select existing, descriptive photographs for generated page templates."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_IMAGE = "technician-thermal-fogging-outdoor-area.webp"

_IMAGE_POOLS = {
    "ant": ("ant-gel-bait-commercialarea.webp",),
    "bed-bug": ("bedbugs.webp",),
    "cockroach": (
        "cockroach-bait-hotelroom.webp",
        "cockroach-gel-baiting-pantry.webp",
        "cockroach-infestation.webp",
        "cockroach-spray-hotelroom.webp",
        "cockroach-spray-residential-hall.webp",
        "cockroach-spray-residential-kitchen.webp",
        "dead-american-cockroach-close-up.webp",
    ),
    "fly": (
        "fly-granular-baiting-cafe.webp",
        "fly-spray-hotel-hall.webp",
        "fly-spray-restaurant-indoor.webp",
    ),
    "fogging": (
        "fogging-warehouse-interior.webp",
        "masquito-spray-commerical-office.webp",
        "mosquito-fogging-jaipur.webp",
        "technician-thermal-fogging-outdoor-area.webp",
        "technician-ulv-fogging-factory.webp",
        "thermal-fogging-commercial-factory.webp",
        "thermal-fogging-corridor.webp",
        "thermal-fogging-factory.webp",
        "thermal-fogging-office.webp",
        "thermal-fogging-showroom.webp",
        "ulv-cold-fogging-machine-in-use.webp",
    ),
    "rodent": (
        "rat-caught-on-glue-pad.webp",
        "rodent-caught-on-glue-trap-warehouse.webp",
        "rodent-entry-point-wall-hole.webp",
        "rodent-glue-pad-close-up.webp",
        "rodent-glue-pad-placed-along-wall.webp",
    ),
    "spider": (
        "spider-close-up-on-wall.webp",
        "spider-spray-under-bed.webp",
        "spider-spray-warehouse.webp",
    ),
    "termite": (
        "drilling-holes-for-termite-treatment.webp",
        "technician-inspecting-warehouse-for-termites.webp",
        "termite-damage-wooden-cupboard.webp",
        "termite-mud-tubes-on-wall.webp",
        "termite-treatment-electrical-board-power-off.webp",
        "termite-treatment-spray-wood-frame.webp",
        "termite-treatment-spray-wood-frame-2.webp",
        "termiticide-injection-along-wall.webp",
    ),
    "wasp": (
        "wasp-nest-balcony-ceiling-after.webp",
        "wasp-nest-balcony-ceiling-before.webp",
    ),
    "wood-borer": (
        "wood-borer-beetle-close-up.webp",
        "wood-borer-treatment-spray-furniture.webp",
        "wood-borer-treatment-warehouse-jaipur.webp",
    ),
    "general": (
        "spray-warehouse.webp",
        "technician-thermal-fogging-outdoor-area.webp",
        "technician-ulv-fogging-factory.webp",
    ),
}

_TOPIC_IMAGES = (
    (r"\b(?:ants?)\b", "ant"),
    (r"\b(?:rodents?|rats?|mice)\b", "rodent"),
    (r"\b(?:termites?|anti.?termite|termite.?piping)\b", "termite"),
    (r"\b(?:bed.?bugs?)\b", "bed-bug"),
    (r"\b(?:cockroach(?:es)?|roach(?:es)?)\b", "cockroach"),
    (r"\b(?:fly|flies|fly.?management)\b", "fly"),
    (r"\b(?:mosquito(?:es)?|vectors?|fogging|ulv)\b", "fogging"),
    (r"\b(?:wasps?|hornets?)\b", "wasp"),
    (r"\b(?:spiders?)\b", "spider"),
    (r"\b(?:wood.?borers?)\b", "wood-borer"),
    (r"\b(?:hotels?|guests?|hostels?|pgs?|resorts?)\b", "bed-bug"),
    (r"\b(?:restaurants?|kitchens?|food)\b", "cockroach"),
    (r"\b(?:warehouses?|godowns?)\b", "fogging"),
    (r"\b(?:factories|factory|industrial)\b", "fogging"),
    (r"\b(?:offices?|commercial)\b", "fogging"),
    (r"\b(?:hospitals?|clinics?|healthcare|health care)\b", "fogging"),
    (r"\b(?:schools?|colleges?|education|venues?|farmhouses?)\b", "general"),
)

_IMAGE_ALTS = {
    "ant-gel-bait-commercialarea.webp": "Technician applying ant gel bait along a commercial service area.",
    "bedbugs.webp": "Bed bug on fabric, illustrating a pest concern relevant to accommodation.",
    "cockroach-bait-hotelroom.webp": "Cockroach bait applied in a hotel room service area.",
    "cockroach-gel-baiting-pantry.webp": "Technician placing cockroach gel bait beside a pantry fixture.",
    "cockroach-infestation.webp": "Cockroach activity near a commercial property surface during inspection.",
    "cockroach-spray-hotelroom.webp": "Pest technician treating a hotel room for cockroach activity.",
    "cockroach-spray-residential-hall.webp": "Technician treating a residential hall for cockroach activity.",
    "cockroach-spray-residential-kitchen.webp": "Technician applying cockroach spray in a residential kitchen.",
    "dead-american-cockroach-close-up.webp": "Close-up of a dead American cockroach, an example of pest evidence for inspection.",
    "drilling-holes-for-termite-treatment.webp": "Technician carefully drilling wall holes for termite treatment.",
    "fly-granular-baiting-cafe.webp": "Granular fly bait placed in a cafe service area.",
    "fly-spray-hotel-hall.webp": "Technician applying fly control treatment in a hotel hall.",
    "fly-spray-restaurant-indoor.webp": "Fly-control spray applied inside a restaurant service area.",
    "fogging-warehouse-interior.webp": "Pest-control fogging treatment inside a warehouse storage area.",
    "masquito-spray-commerical-office.webp": "Technician spraying for mosquitoes in a commercial office.",
    "mosquito-fogging-jaipur.webp": "Mosquito fogging carried out along an outdoor street in Jaipur.",
    "rat-caught-on-glue-pad.webp": "Rat caught on a glue pad during a rodent-control inspection.",
    "rodent-caught-on-glue-trap-warehouse.webp": "Rodent caught on a glue trap in a warehouse.",
    "rodent-entry-point-wall-hole.webp": "Damaged wall opening that may provide pest access.",
    "rodent-glue-pad-close-up.webp": "Close view of a rodent monitoring glue pad.",
    "rodent-glue-pad-placed-along-wall.webp": "Glue monitoring pad positioned along an interior wall.",
    "spider-close-up-on-wall.webp": "Spider on an indoor wall, shown as an example for pest inspection.",
    "spider-spray-under-bed.webp": "Spider treatment applied beneath a residential bed frame.",
    "spider-spray-warehouse.webp": "Spider spray applied in a warehouse service area.",
    "spray-warehouse.webp": "Palletized goods stored inside a commercial warehouse facility.",
    "technician-inspecting-warehouse-for-termites.webp": "Technician inspecting a warehouse for visible termite activity.",
    "technician-thermal-fogging-outdoor-area.webp": "Technician using thermal fogging in an outdoor service area.",
    "technician-ulv-fogging-factory.webp": "Technician operating ULV fogging equipment inside a factory.",
    "termite-damage-wooden-cupboard.webp": "Termite damage visible inside a wooden storage cupboard.",
    "termite-mud-tubes-on-wall.webp": "Termite mud tubes extending along an interior wall.",
    "termite-treatment-electrical-board-power-off.webp": "Termite treatment performed near a switched-off electrical board.",
    "termite-treatment-spray-wood-frame.webp": "Termite treatment applied along a wooden door frame.",
    "termite-treatment-spray-wood-frame-2.webp": "Technician spraying a timber frame during termite treatment.",
    "termiticide-injection-along-wall.webp": "Termiticide injected beside an interior wall during treatment.",
    "thermal-fogging-commercial-factory.webp": "Thermal fogging in a commercial factory service area.",
    "thermal-fogging-corridor.webp": "Thermal fogging applied through an indoor building corridor.",
    "thermal-fogging-factory.webp": "Fogging treatment carried out inside an industrial factory.",
    "thermal-fogging-office.webp": "Pest control fogging performed inside a commercial office.",
    "thermal-fogging-showroom.webp": "Thermal fogging applied inside a commercial furniture showroom.",
    "ulv-cold-fogging-machine-in-use.webp": "ULV cold fogging machine operating during pest treatment.",
    "wasp-nest-balcony-ceiling-after.webp": "Wasp nest attached beneath an apartment balcony ceiling.",
    "wasp-nest-balcony-ceiling-before.webp": "Wasp nest visible below a balcony ceiling before removal.",
    "wood-borer-beetle-close-up.webp": "Wood-boring beetle shown close-up during a pest assessment visit.",
    "wood-borer-treatment-spray-furniture.webp": "Wood-borer treatment applied to a wooden furniture surface.",
    "wood-borer-treatment-spray-furniture-02.webp": "Wood-borer treatment applied to a wooden furniture surface.",
    "wood-borer-treatment-warehouse-jaipur.webp": "Wooden materials stored in a warehouse during wood-borer treatment.",
}

_DISTRICT_IMAGES = {
    "ajmer": "ajmer-1400.webp",
    "didwana-kuchaman": "didwana.webp",
    "khairthal-tijara": "tijara.webp",
    "kotputli-behror": "kotputli.webp",
    "sawai-madhopur": "sawai.webp",
    "salumber": "salumbar.webp",
}


def _category_for_topic(topic: str) -> str:
    normalized = topic.casefold().replace("_", " ").replace("-", " ")
    return next(
        (
            category
            for pattern, category in _TOPIC_IMAGES
            if re.search(pattern, normalized)
        ),
        "general",
    )


def select_topic_images(
    topic: str,
    page_slug: str,
    count: int = 1,
    exclude: tuple[str, ...] | set[str] = (),
) -> list[tuple[str, str]]:
    """Select distinct topic-matched images deterministically for a page."""
    if count < 1:
        return []
    category = _category_for_topic(topic)
    pools = [_IMAGE_POOLS[category]]
    if category != "general":
        pools.append(_IMAGE_POOLS["general"])
    excluded = {unquote(item).rsplit("/", 1)[-1] for item in exclude}
    selected: list[str] = []
    for pool_index, pool in enumerate(pools):
        remaining = [item for item in pool if item not in excluded and item not in selected]
        if not remaining:
            continue
        seed = f"{page_slug.casefold()}|{category}|{pool_index}"
        offset = int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:4], "big")
        remaining = remaining[offset % len(remaining):] + remaining[:offset % len(remaining)]
        selected.extend(remaining[:count - len(selected)])
        if len(selected) >= count:
            break
    return [(filename, _IMAGE_ALTS[filename]) for filename in selected]


def image_for_topic(
    topic: str,
    page_slug: str = "",
    exclude: tuple[str, ...] | set[str] = (),
) -> tuple[str, str]:
    """Return one existing image filename and alt text matching a page topic."""
    images = select_topic_images(topic, page_slug, 1, exclude)
    if images:
        return images[0]
    return DEFAULT_IMAGE, _IMAGE_ALTS[DEFAULT_IMAGE]


def image_dimensions(filename: str) -> tuple[int, int]:
    """Read intrinsic dimensions from a local WebP file header."""
    decoded = unquote(filename).rsplit("/", 1)[-1]
    source = ROOT / "images" / decoded
    if not source.is_file():
        source = ROOT / "webp-images" / decoded
    data = source.read_bytes()
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError(f"Not a supported WebP image: {source}")
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
    elif chunk == b"VP8L":
        width = 1 + data[21] + ((data[22] & 0x3F) << 8)
        height = 1 + (data[22] >> 6) + (data[23] << 2) + ((data[24] & 0x0F) << 10)
    elif chunk == b"VP8 ":
        width = int.from_bytes(data[26:28], "little") & 0x3FFF
        height = int.from_bytes(data[28:30], "little") & 0x3FFF
    else:
        raise ValueError(f"Unsupported WebP chunk {chunk!r}: {source}")
    return width, height


def image_for_district(district: str) -> tuple[str, str]:
    """Use a district photo when available, otherwise a truthful service photo."""
    slug = re.sub(r"[^a-z0-9]+", "-", district.casefold()).strip("-")
    filename = _DISTRICT_IMAGES.get(slug, f"{slug}.webp")
    if not (ROOT / "images" / filename).is_file():
        return image_for_topic("")
    return filename, f"Representative view of {district}, Rajasthan, illustrating the local service area."
