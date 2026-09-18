"""Travel scraper package: Scrapy spider + ETL for Wikivoyage listings."""

from __future__ import annotations

from pathlib import Path

from travel_scraper.destinations import (
    DEFAULT_DESTINATIONS_FILE,
    Destination,
    build_lookup,
    destinations_to_payload,
    load_default_destinations,
    load_destinations_file,
)
from travel_scraper.destinations import (
    resolve_country as resolve_country_with_registry,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

# Demo destinations come from config/demo_destinations.json (explicit country metadata).
DEFAULT_DESTINATIONS: tuple[Destination, ...] = tuple(load_default_destinations())
DEFAULT_DESTINATION_NAMES: tuple[str, ...] = tuple(d.name for d in DEFAULT_DESTINATIONS)
_DESTINATION_BY_NAME: dict[str, Destination] = build_lookup(list(DEFAULT_DESTINATIONS))


def lookup_destination(name: str) -> Destination | None:
    """Return a known destination from the demo config, or None."""
    return _DESTINATION_BY_NAME.get(name.strip().casefold())


def resolve_country(destination_name: str, explicit_country: str | None = None) -> str | None:
    """Resolve country using explicit metadata or the loaded demo registry.

    Never invents a country for unknown destinations.
    """
    return resolve_country_with_registry(
        destination_name,
        explicit_country=explicit_country,
        registry=_DESTINATION_BY_NAME,
    )


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

__all__ = [
    "CATEGORY_ALIASES",
    "DEFAULT_DESTINATIONS",
    "DEFAULT_DESTINATIONS_FILE",
    "DEFAULT_DESTINATION_NAMES",
    "DESCRIPTION_MAX_CHARS",
    "Destination",
    "PACKAGE_ROOT",
    "PROJECT_ROOT",
    "SUPPORTED_CATEGORIES",
    "WIKIVOYAGE_BASE",
    "build_lookup",
    "destinations_to_payload",
    "load_default_destinations",
    "load_destinations_file",
    "lookup_destination",
    "resolve_country",
]
