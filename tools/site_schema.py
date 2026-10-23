"""Shared structured data for the Super Pest Control website entity."""

from __future__ import annotations

SITE_URL = "https://www.superpest.in/"
BUSINESS_ID = f"{SITE_URL}#business"
WEBSITE_ID = f"{SITE_URL}#website"
SITE_DESCRIPTION = (
    "Professional residential and commercial pest control services across Rajasthan."
)

SOCIAL_PROFILES = [
    "https://www.facebook.com/p/Super-Pest-Control-Services-100075474775254/",
    "https://www.instagram.com/superpestcontrolservices?igsh=YzM3cmN0b2EwdGxh",
    "https://x.com/Superpestcontro",
    "https://www.linkedin.com/in/kishor-singh-10866a252/",
]


def website_schema() -> dict[str, object]:
    return {
        "@type": "WebSite",
        "@id": WEBSITE_ID,
        "url": SITE_URL,
        "name": "Super Pest Control Services",
        "description": SITE_DESCRIPTION,
        "publisher": {"@id": BUSINESS_ID},
        "sameAs": SOCIAL_PROFILES,
        "potentialAction": {
            "@type": "CommunicateAction",
            "target": f"{SITE_URL}contact/",
        },
    }
