"""Parser unit tests using offline HTML fixtures."""

from __future__ import annotations

from pathlib import Path

from travel_scraper.parsing import parse_destination_html

FIXTURE = Path(__file__).parent / "fixtures" / "listing_page.html"


def test_parse_extracts_supported_listings_only() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    records = parse_destination_html(
        html,
        destination="Fixture City",
        country="Morocco",
        source_url="https://en.wikivoyage.org/wiki/Fixture_City",
        scraped_at="2026-01-01T00:00:00+00:00",
    )
    assert len(records) == 2
    names = {r["name"] for r in records}
    assert names == {"Blue Mosque", "Street Café"}
    assert all(r["category"] in {"see", "eat"} for r in records)


def test_parse_fields_from_see_listing() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    records = parse_destination_html(
        html,
        destination="Fixture City",
        country="Morocco",
        source_url="https://en.wikivoyage.org/wiki/Fixture_City",
        scraped_at="2026-01-01T00:00:00+00:00",
    )
    see = next(r for r in records if r["category"] == "see")
    assert see["latitude"] == "31.62500"
    assert see["longitude"] == "-7.98900"
    assert see["address"] == "1 Medina Street"
    assert see["phone"] in {"+212 524 000 001", "+212524000001"}
    assert see["email"] == "info@example.org"
    assert see["website"] == "https://example.org/blue-mosque"
    assert see["opening_hours"] == "09:00–17:00"
    assert see["price"] == "50 dirham"
    assert see["source_listing_id"] == "Blue_Mosque"


def test_parse_subcategory_from_h3() -> None:
    html = FIXTURE.read_text(encoding="utf-8")
    records = parse_destination_html(
        html,
        destination="Fixture City",
        country="Morocco",
        source_url="https://en.wikivoyage.org/wiki/Fixture_City",
        scraped_at="2026-01-01T00:00:00+00:00",
    )
    eat = next(r for r in records if r["category"] == "eat")
    assert eat["subcategory"] == "Budget"
    assert eat["website"] is None
    assert eat["latitude"] is None
