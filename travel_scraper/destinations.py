"""Destination configuration loading for worldwide Wikivoyage crawls."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
DEFAULT_DESTINATIONS_FILE = PROJECT_ROOT / "config" / "demo_destinations.json"


@dataclass(frozen=True, slots=True)
class Destination:
    """A Wikivoyage destination page and its explicit country metadata."""

    name: str
    country: str


def _normalize_entry(raw: object, *, index: int) -> Destination:
    if not isinstance(raw, dict):
        raise ValueError(f"Destination entry at index {index} must be an object")
    name = raw.get("name")
    country = raw.get("country")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"Destination entry at index {index} requires a non-empty name")
    if not isinstance(country, str) or not country.strip():
        raise ValueError(
            f"Destination '{name}' requires an explicit country; never invent country metadata"
        )
    return Destination(name=name.strip(), country=country.strip())


def load_destinations_file(path: Path | str | None = None) -> list[Destination]:
    """Load destination/country pairs from a JSON configuration file."""
    config_path = Path(path) if path is not None else DEFAULT_DESTINATIONS_FILE
    if not config_path.is_file():
        raise FileNotFoundError(f"Destinations file not found: {config_path}")
    try:
        payload = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid destinations JSON in {config_path}: {exc}") from exc
    if not isinstance(payload, list) or not payload:
        raise ValueError(f"Destinations file must contain a non-empty JSON array: {config_path}")
    return [_normalize_entry(item, index=i) for i, item in enumerate(payload)]


def destinations_to_payload(destinations: list[Destination]) -> list[dict[str, str]]:
    """Serialize destinations for spider arguments / crawl metadata."""
    return [asdict(d) for d in destinations]


def build_lookup(destinations: list[Destination]) -> dict[str, Destination]:
    """Case-insensitive name → Destination map (last write wins on duplicates)."""
    return {d.name.casefold(): d for d in destinations}


def resolve_country(
    destination_name: str,
    *,
    explicit_country: str | None = None,
    registry: dict[str, Destination] | None = None,
) -> str | None:
    """Resolve country for a destination without inventing metadata.

    Prefer an explicit country. Otherwise use the provided registry (typically
    loaded from a destinations file). Unknown names return None.
    """
    if explicit_country and explicit_country.strip():
        return explicit_country.strip()
    if registry is None:
        return None
    known = registry.get(destination_name.strip().casefold())
    return known.country if known else None


def load_default_destinations() -> list[Destination]:
    """Load the repository's demo destination configuration."""
    return load_destinations_file(DEFAULT_DESTINATIONS_FILE)
