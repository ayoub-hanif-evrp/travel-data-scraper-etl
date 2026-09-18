"""Deduplication and stable ID tests."""

from travel_scraper.deduplication import deduplicate_records, identity_key, make_record_id


def test_identity_key_uses_coords_when_present() -> None:
    a = {
        "destination": "Marrakech",
        "name": "Blue Mosque",
        "latitude": 31.625001,
        "longitude": -7.989002,
        "category": "see",
    }
    b = {
        "destination": "marrakech",
        "name": "blue   mosque",
        "latitude": 31.62500,
        "longitude": -7.98900,
        "category": "see",
    }
    assert identity_key(a) == identity_key(b)


def test_deduplicate_keeps_first() -> None:
    records = [
        {
            "destination": "Fes",
            "name": "Cafe",
            "category": "eat",
            "address": "Main St",
            "latitude": None,
            "longitude": None,
        },
        {
            "destination": "Fes",
            "name": "Cafe",
            "category": "eat",
            "address": "Main St",
            "latitude": None,
            "longitude": None,
            "price": "extra",
        },
    ]
    result = deduplicate_records(records)
    assert result.final_count == 1
    assert result.duplicates_removed == 1
    # First occurrence kept (no price on the first record)
    assert result.records[0].get("price") != "extra"


def test_stable_record_ids() -> None:
    record = {
        "destination": "Rabat",
        "name": "Kasbah",
        "category": "see",
        "latitude": 34.03,
        "longitude": -6.84,
    }
    assert make_record_id(record) == make_record_id(dict(record))
    assert len(make_record_id(record)) == 16
