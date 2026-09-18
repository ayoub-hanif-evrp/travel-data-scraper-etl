"""Travel scraper package: Scrapy spider + ETL for Wikivoyage listings."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent


@dataclass(frozen=True, slots=True)
class Destination:
    """A configured Wikivoyage destination page and its country."""

    name: str
    country: str


# Small multi-country demonstration set (not a full-site crawl).
DEFAULT_DESTINATIONS: tuple[Destination, ...] = (
    Destination("Marrakech", "Morocco"),
    Destination("Paris", "France"),
    Destination("Barcelona", "Spain"),
    Destination("Rome", "Italy"),
    Destination("Istanbul", "Turkey"),
    Destination("Bangkok", "Thailand"),
)

DEFAULT_DESTINATION_NAMES: tuple[str, ...] = tuple(d.name for d in DEFAULT_DESTINATIONS)

_DESTINATION_BY_NAME: dict[str, Destination] = {
    d.name.casefold(): d for d in DEFAULT_DESTINATIONS
}


def lookup_destination(name: str) -> Destination | None:
    """Return a known destination config, or None if the name is not configured."""
    return _DESTINATION_BY_NAME.get(name.strip().casefold())


def resolve_country(destination_name: str, explicit_country: str | None = None) -> str | None:
    """Resolve country for a destination.

    Prefer an explicit CLI/config country when provided. Otherwise use the
    configured default set. Unknown custom destinations return None (never
    invent a country such as Morocco).
    """
    if explicit_country and explicit_country.strip():
        return explicit_country.strip()
    known = lookup_destination(destination_name)
    return known.country if known else None


SUPPORTED_CATEGORIES: frozenset[str] = frozenset(
    {"see", "do", "buy", "eat", "drink", "sleep"}
)

CATEGORY_ALIASES: dict[str, str] = {
    "see": "see",
    "do": "do",
    "buy": "buy",
    "eat": "eat",
    "drink": "drink",
    "sleep": "sleep",
    "go": "do",
    "view": "see",
    "listing": "see",
}

WIKIVOYAGE_BASE = "https://en.wikivoyage.org/wiki/"

DESCRIPTION_MAX_CHARS = 400
