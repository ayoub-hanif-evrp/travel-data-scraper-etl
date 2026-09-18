"""Validation tests."""

from travel_scraper.validation import validate_record, validate_records


def _base(**overrides):
    record = {
        "name": "Place",
        "destination": "Rabat",
        "category": "see",
        "source_url": "https://en.wikivoyage.org/wiki/Rabat",
        "scraped_at": "2026-01-01T00:00:00+00:00",
        "latitude": 34.0,
        "longitude": -6.8,
        "website": "https://example.com",
    }
    record.update(overrides)
    return record


def test_valid_record() -> None:
    assert validate_record(_base()) == []


def test_missing_name() -> None:
    assert "missing_name" in validate_record(_base(name=None))


def test_invalid_placeholder_name() -> None:
    reasons = validate_record(_base(name="["))
    assert "invalid_name" in reasons


def test_invalid_coordinates() -> None:
    reasons = validate_record(_base(latitude=120.0))
    assert "invalid_latitude" in reasons


def test_incomplete_coordinates() -> None:
    reasons = validate_record(_base(longitude=None))
    assert "incomplete_coordinates" in reasons


def test_invalid_website() -> None:
    reasons = validate_record(_base(website="ftp://example.com"))
    assert "invalid_website" in reasons


def test_unsupported_category() -> None:
    reasons = validate_record(_base(category="understand"))
    assert "unsupported_category" in reasons


def test_validate_records_tracks_rejects() -> None:
    result = validate_records([_base(), _base(name=None)])
    assert result.valid_count == 1
    assert result.invalid_count == 1
    assert result.rejection_reasons["missing_name"] == 1
