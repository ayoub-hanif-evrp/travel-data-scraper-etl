"""Destination configuration helpers."""

from travel_scraper import (
    DEFAULT_DESTINATIONS,
    lookup_destination,
    resolve_country,
)


def test_default_destinations_are_international() -> None:
    countries = {d.country for d in DEFAULT_DESTINATIONS}
    assert "Morocco" in countries
    assert "France" in countries
    assert "Spain" in countries
    assert "Italy" in countries
    assert "Turkey" in countries
    assert "Thailand" in countries
    assert len(DEFAULT_DESTINATIONS) == 6


def test_lookup_and_resolve_country() -> None:
    assert lookup_destination("paris") is not None
    assert resolve_country("Paris") == "France"
    assert resolve_country("Unknown City") is None
    assert resolve_country("Unknown City", explicit_country="Japan") == "Japan"
