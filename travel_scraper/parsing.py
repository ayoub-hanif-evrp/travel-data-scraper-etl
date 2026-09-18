"""HTML parsing helpers for Wikivoyage listing vcards.

Selectors target semantic classes observed on live English Wikivoyage pages
(``bdi.vcard``, ``.listing-name``, ``.geo``, etc.). Category prefers the
Kartographer maplink ``group`` attribute, then falls back to the nearest ``h2``.
"""

from __future__ import annotations

import json
import re
from html import unescape
from typing import Any
from urllib.parse import urljoin

from travel_scraper import (
    CATEGORY_ALIASES,
    DESCRIPTION_MAX_CHARS,
    SUPPORTED_CATEGORIES,
)

# Optional dependency at import time for unit tests without Scrapy Selector —
# scrapy.Selector is used when available; tests can pass prebuilt selectors.
try:
    from scrapy.http import TextResponse
    from scrapy.selector import Selector
except ImportError:  # pragma: no cover
    TextResponse = None  # type: ignore[misc, assignment]
    Selector = None  # type: ignore[misc, assignment]


_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)
_SECTION_CATEGORY = {
    "See": "see",
    "Do": "do",
    "Buy": "buy",
    "Eat": "eat",
    "Drink": "drink",
    "Sleep": "sleep",
}


def _collapse_ws(text: str | None) -> str | None:
    if text is None:
        return None
    cleaned = _WHITESPACE_RE.sub(" ", unescape(text)).strip()
    return cleaned or None


def _first_text(node: Any, css: str) -> str | None:
    values = node.css(css).getall()
    for value in values:
        cleaned = _collapse_ws(value)
        if cleaned:
            return cleaned
    return None


def _extract_website(vcard: Any) -> str | None:
    hrefs = vcard.css(".listing-name a.external::attr(href)").getall()
    for href in hrefs:
        href = (href or "").strip()
        if href.startswith(("http://", "https://")):
            return href
    return None


def _extract_email(vcard: Any) -> str | None:
    mailto = vcard.css(".listing-email a::attr(href)").get()
    if mailto and mailto.lower().startswith("mailto:"):
        return _collapse_ws(mailto[7:].split("?")[0])
    return _first_text(vcard, ".listing-email ::text")


def _extract_phone(vcard: Any) -> str | None:
    tel = vcard.css(".listing-phone a::attr(href)").get()
    if tel and tel.lower().startswith("tel:"):
        return _collapse_ws(tel[4:])
    return _first_text(vcard, ".listing-phone ::text")


def _extract_coordinates(vcard: Any) -> tuple[str | None, str | None]:
    lat = _first_text(vcard, ".geo .latitude::text")
    lon = _first_text(vcard, ".geo .longitude::text")
    if lat and lon:
        return lat, lon
    maplink = vcard.css("a.mw-kartographer-maplink")
    if maplink:
        lat = maplink.attrib.get("data-lat") or lat
        lon = maplink.attrib.get("data-lon") or lon
    return lat, lon


def _category_from_maplink(vcard: Any) -> str | None:
    maplink = vcard.css("a.mw-kartographer-maplink")
    if not maplink:
        return None
    data_mw = maplink.attrib.get("data-mw")
    if not data_mw:
        return None
    try:
        payload = json.loads(data_mw)
    except json.JSONDecodeError:
        return None
    group = (payload.get("attrs") or {}).get("group")
    if not group:
        return None
    return CATEGORY_ALIASES.get(str(group).lower())


def _nearest_heading_category(vcard: Any) -> str | None:
    """Walk preceding headings in document order via XPath."""
    headings = vcard.xpath(
        "preceding::h2[1]//span[@class='mw-headline']/@id"
        " | preceding::h2[1]/@id"
        " | preceding::*[contains(@class,'mw-heading2')][1]//h2/@id"
    ).getall()
    for heading_id in headings:
        if heading_id in _SECTION_CATEGORY:
            return _SECTION_CATEGORY[heading_id]
        # Some pages use id on the headline span
        key = heading_id.replace("_", " ")
        if key in _SECTION_CATEGORY:
            return _SECTION_CATEGORY[key]
    # Fallback: text of nearest h2
    texts = vcard.xpath("preceding::h2[1]//text()").getall()
    label = _collapse_ws(" ".join(texts) or "")
    if label:
        for known, category in _SECTION_CATEGORY.items():
            if label.startswith(known):
                return category
    return None


def _nearest_subcategory(vcard: Any) -> str | None:
    texts = vcard.xpath(
        "preceding::h3[1]//span[contains(@class,'mw-headline')]/text()"
        " | preceding::h3[1]//text()"
    ).getall()
    label = _collapse_ws(" ".join(texts) if texts else None)
    if not label:
        return None
    # Drop edit links / brackets noise
    label = re.sub(r"\[.*?\]", "", label).strip()
    return label or None


def _source_listing_id(vcard: Any) -> str | None:
    name_id = vcard.css(".listing-name::attr(id)").get()
    if name_id:
        return _collapse_ws(name_id)
    return vcard.attrib.get("id")


def parse_vcard(
    vcard: Any,
    *,
    destination: str,
    country: str | None,
    source_url: str,
    scraped_at: str,
) -> dict[str, Any] | None:
    """Parse a single ``bdi.vcard`` node into a raw listing dict."""
    name = _first_text(vcard, ".listing-name ::text")
    if not name:
        return None

    category = _category_from_maplink(vcard) or _nearest_heading_category(vcard)
    if category not in SUPPORTED_CATEGORIES:
        return None

    lat, lon = _extract_coordinates(vcard)
    description = _first_text(vcard, ".listing-content ::text")
    if description and len(description) > DESCRIPTION_MAX_CHARS:
        description = description[: DESCRIPTION_MAX_CHARS - 1].rstrip() + "…"

    return {
        "destination": destination,
        "country": country,
        "category": category,
        "subcategory": _nearest_subcategory(vcard),
        "name": name,
        "address": _first_text(vcard, ".listing-address ::text"),
        "latitude": lat,
        "longitude": lon,
        "phone": _extract_phone(vcard),
        "email": _extract_email(vcard),
        "website": _extract_website(vcard),
        "opening_hours": _first_text(vcard, ".listing-hours ::text"),
        "price": _first_text(vcard, ".listing-price ::text"),
        "description": description,
        "source_url": source_url,
        "source_listing_id": _source_listing_id(vcard),
        "scraped_at": scraped_at,
    }


def parse_destination_html(
    html: str,
    *,
    destination: str,
    country: str | None,
    source_url: str,
    scraped_at: str,
    base_url: str = "https://en.wikivoyage.org",
) -> list[dict[str, Any]]:
    """Parse all supported listings from a destination page HTML string."""
    if Selector is None:
        raise RuntimeError("scrapy is required to parse HTML")

    # Absolute-ize relative links for consistent website extraction
    response = TextResponse(
        url=source_url or urljoin(base_url, "/"),
        body=html.encode("utf-8"),
        encoding="utf-8",
    )
    records: list[dict[str, Any]] = []
    for vcard in response.css("bdi.vcard"):
        record = parse_vcard(
            vcard,
            destination=destination,
            country=country,
            source_url=source_url,
            scraped_at=scraped_at,
        )
        if record:
            records.append(record)
    return records
