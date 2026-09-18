"""Normalization helpers for raw travel listing records."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse, urlunparse

from travel_scraper import CATEGORY_ALIASES, SUPPORTED_CATEGORIES

_WHITESPACE_RE = re.compile(r"[\s\u00a0\u2000-\u200b\u202f\u205f\u3000]+", re.UNICODE)
_PHONE_KEEP_RE = re.compile(r"[^\d+()\-\s.]")


def normalize_whitespace(value: Any) -> str | None:
    """Collapse Unicode whitespace; empty strings become None."""
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = _WHITESPACE_RE.sub(" ", value).strip()
    return cleaned or None


def normalize_destination(value: Any) -> str | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    # Title-case words but preserve known casing like "Fes"
    return " ".join(part.capitalize() if part.islower() else part for part in text.split())


def normalize_category(value: Any) -> str | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    key = text.lower()
    mapped = CATEGORY_ALIASES.get(key, key)
    if mapped in SUPPORTED_CATEGORIES:
        return mapped
    return mapped  # leave for validation to reject


def normalize_url(value: Any) -> str | None:
    text = normalize_whitespace(value)
    if not text:
        return None
    if text.startswith("//"):
        text = "https:" + text
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        return text  # leave as-is; validation decides
    # Lowercase scheme/host; drop fragments; keep path/query
    netloc = parsed.netloc.lower()
    path = parsed.path or ""
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/")
    return urlunparse((parsed.scheme.lower(), netloc, path, "", parsed.query, ""))


def normalize_phone(value: Any) -> str | None:
    """Conservative phone cleanup — strip junk, keep digits and common symbols."""
    text = normalize_whitespace(value)
    if not text:
        return None
    cleaned = _PHONE_KEEP_RE.sub("", text)
    cleaned = normalize_whitespace(cleaned)
    return cleaned


def normalize_coordinate(value: Any) -> float | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = normalize_whitespace(str(value))
    if not text:
        return None
    try:
        return float(text.replace(",", "."))
    except ValueError:
        return None


def clean_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a cleaned copy of a raw listing dict."""
    return {
        "destination": normalize_destination(raw.get("destination")),
        "country": normalize_whitespace(raw.get("country")),
        "category": normalize_category(raw.get("category")),
        "subcategory": normalize_whitespace(raw.get("subcategory")),
        "name": normalize_whitespace(raw.get("name")),
        "address": normalize_whitespace(raw.get("address")),
        "latitude": normalize_coordinate(raw.get("latitude")),
        "longitude": normalize_coordinate(raw.get("longitude")),
        "phone": normalize_phone(raw.get("phone")),
        "email": normalize_whitespace(raw.get("email")),
        "website": normalize_url(raw.get("website")),
        "opening_hours": normalize_whitespace(raw.get("opening_hours")),
        "price": normalize_whitespace(raw.get("price")),
        "description": normalize_whitespace(raw.get("description")),
        "source_url": normalize_url(raw.get("source_url")),
        "source_listing_id": normalize_whitespace(raw.get("source_listing_id")),
        "scraped_at": normalize_whitespace(raw.get("scraped_at")),
    }


def clean_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [clean_record(r) for r in records]
