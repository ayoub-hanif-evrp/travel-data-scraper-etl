"""Destination configuration helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from travel_scraper import (
    DEFAULT_DESTINATIONS,
    DEFAULT_DESTINATIONS_FILE,
    Destination,
    load_destinations_file,
    lookup_destination,
    resolve_country,
)
from travel_scraper.destinations import build_lookup
from travel_scraper.destinations import resolve_country as resolve_with_registry


def test_default_destinations_are_worldwide() -> None:
    countries = {d.country for d in DEFAULT_DESTINATIONS}
    assert "Morocco" in countries
    assert "France" in countries
    assert "Japan" in countries
    assert "United States" in countries
    assert "Australia" in countries
    assert "South Africa" in countries
    assert "Argentina" in countries
    assert len(DEFAULT_DESTINATIONS) >= 10
    assert all(d.name and d.country for d in DEFAULT_DESTINATIONS)


def test_destinations_file_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "custom.json"
    path.write_text(
        json.dumps(
            [
                {"name": "Lisbon", "country": "Portugal"},
                {"name": "Cairo", "country": "Egypt"},
            ]
        ),
        encoding="utf-8",
    )
    loaded = load_destinations_file(path)
    assert loaded == [
        Destination("Lisbon", "Portugal"),
        Destination("Cairo", "Egypt"),
    ]
    registry = build_lookup(loaded)
    assert resolve_with_registry("lisbon", registry=registry) == "Portugal"
    assert resolve_with_registry("Unknown", registry=registry) is None


def test_destinations_file_requires_country(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"name": "Nowhere"}]), encoding="utf-8")
    with pytest.raises(ValueError, match="explicit country"):
        load_destinations_file(path)


def test_lookup_and_resolve_country() -> None:
    assert lookup_destination("tokyo") is not None
    assert resolve_country("Tokyo") == "Japan"
    assert resolve_country("Unknown City") is None
    assert resolve_country("Unknown City", explicit_country="Japan") == "Japan"
    assert DEFAULT_DESTINATIONS_FILE.is_file()
