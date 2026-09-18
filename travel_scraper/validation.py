"""Explicit validation for cleaned travel listings."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from travel_scraper import SUPPORTED_CATEGORIES


@dataclass
class ValidationResult:
    valid: list[dict[str, Any]] = field(default_factory=list)
    invalid: list[dict[str, Any]] = field(default_factory=list)
    rejection_reasons: dict[str, int] = field(default_factory=dict)

    @property
    def valid_count(self) -> int:
        return len(self.valid)

    @property
    def invalid_count(self) -> int:
        return len(self.invalid)


def _is_valid_http_url(value: str | None, *, required: bool = False) -> bool:
    if value is None:
        return not required
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_record(record: dict[str, Any]) -> list[str]:
    """Return a list of rejection reasons (empty if valid)."""
    reasons: list[str] = []

    name = record.get("name")
    if not name:
        reasons.append("missing_name")
    elif isinstance(name, str):
        stripped = name.strip()
        if len(stripped) < 2 or stripped in {"[", "]", "(", ")", "{", "}", "-", "—", "–"} or not any(ch.isalnum() for ch in stripped):
            reasons.append("invalid_name")
    if not record.get("destination"):
        reasons.append("missing_destination")

    category = record.get("category")
    if not category:
        reasons.append("missing_category")
    elif category not in SUPPORTED_CATEGORIES:
        reasons.append("unsupported_category")

    if not record.get("source_url"):
        reasons.append("missing_source_url")
    elif not _is_valid_http_url(record.get("source_url"), required=True):
        reasons.append("invalid_source_url")

    if not record.get("scraped_at"):
        reasons.append("missing_scraped_at")

    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is not None and (
        not isinstance(lat, (int, float)) or not (-90 <= float(lat) <= 90)
    ):
        reasons.append("invalid_latitude")
    if lon is not None and (
        not isinstance(lon, (int, float)) or not (-180 <= float(lon) <= 180)
    ):
        reasons.append("invalid_longitude")
    if (lat is None) ^ (lon is None):
        reasons.append("incomplete_coordinates")

    website = record.get("website")
    if website is not None and not _is_valid_http_url(website):
        reasons.append("invalid_website")

    return reasons


def validate_records(records: list[dict[str, Any]]) -> ValidationResult:
    result = ValidationResult()
    for record in records:
        reasons = validate_record(record)
        if reasons:
            rejected = dict(record)
            rejected["rejection_reasons"] = reasons
            result.invalid.append(rejected)
            for reason in reasons:
                result.rejection_reasons[reason] = result.rejection_reasons.get(reason, 0) + 1
        else:
            result.valid.append(record)
    return result
