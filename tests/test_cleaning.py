"""Cleaning / normalization tests."""

from travel_scraper.cleaning import (
    clean_record,
    normalize_category,
    normalize_coordinate,
    normalize_phone,
    normalize_url,
    normalize_whitespace,
)


def test_whitespace_and_empty() -> None:
    assert normalize_whitespace("  hello   world\u00a0") == "hello world"
    assert normalize_whitespace("   ") is None
    assert normalize_whitespace(None) is None


def test_url_normalization() -> None:
    assert normalize_url("HTTPS://Example.COM/path/") == "https://example.com/path"
    assert normalize_url("//cdn.example.com/a") == "https://cdn.example.com/a"


def test_phone_conservative() -> None:
    assert normalize_phone(" +212 (524) 000-001 ") == "+212 (524) 000-001"


def test_coordinates() -> None:
    assert normalize_coordinate("31.5") == 31.5
    assert normalize_coordinate("bad") is None
    assert normalize_coordinate("") is None


def test_category_normalization() -> None:
    assert normalize_category(" See ") == "see"
    assert normalize_category("GO") == "do"


def test_clean_record_preserves_unicode() -> None:
    cleaned = clean_record(
        {
            "destination": "  fes ",
            "name": "Café Centrale",
            "category": "eat",
            "latitude": "34.0",
            "longitude": "-5.0",
            "source_url": "https://en.wikivoyage.org/wiki/Fes",
            "scraped_at": "2026-01-01T00:00:00+00:00",
            "address": "",
            "website": None,
        }
    )
    assert cleaned["destination"] == "Fes"
    assert cleaned["name"] == "Café Centrale"
    assert cleaned["address"] is None
    assert cleaned["latitude"] == 34.0
