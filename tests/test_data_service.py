"""Data service filtering and metrics tests."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from app.data_service import DataService
from travel_scraper.storage import write_sqlite


def _records() -> list[dict]:
    return [
        {
            "id": "1111111111111111",
            "destination": "Marrakech",
            "country": "Morocco",
            "category": "eat",
            "subcategory": None,
            "name": "Cafe Atlas",
            "address": "Square",
            "latitude": 31.62,
            "longitude": -7.99,
            "phone": None,
            "email": None,
            "website": "https://example.com/cafe",
            "opening_hours": None,
            "price": "cheap",
            "description": "Local cafe",
            "source_url": "https://en.wikivoyage.org/wiki/Marrakech",
            "source_listing_id": "Cafe_Atlas",
            "scraped_at": "2026-01-01T00:00:00+00:00",
        },
        {
            "id": "2222222222222222",
            "destination": "Paris",
            "country": "France",
            "category": "see",
            "subcategory": None,
            "name": "Louvre Gate",
            "address": None,
            "latitude": None,
            "longitude": None,
            "phone": None,
            "email": None,
            "website": None,
            "opening_hours": None,
            "price": None,
            "description": "Historic gate",
            "source_url": "https://en.wikivoyage.org/wiki/Paris",
            "source_listing_id": "Louvre_Gate",
            "scraped_at": "2026-01-01T00:00:00+00:00",
        },
    ]


def test_filter_and_metrics(tmp_path: Path) -> None:
    db = tmp_path / "travel_listings.sqlite"
    write_sqlite(_records(), db)
    service = DataService(sqlite_path=db, sample_csv_path=tmp_path / "missing.csv")
    service.load()
    assert service.source == "sqlite"
    assert service.overview_metrics()["total_listings"] == 2
    assert service.overview_metrics()["countries"] == 2
    assert service.overview_metrics()["with_coordinates"] == 1
    assert service.overview_metrics()["with_website"] == 1

    filtered = service.filter_listings(search="cafe", destinations=["Marrakech"])
    assert len(filtered) == 1
    assert filtered.iloc[0]["name"] == "Cafe Atlas"

    by_country = service.filter_listings(countries=["France"])
    assert len(by_country) == 1
    assert by_country.iloc[0]["destination"] == "Paris"

    cats = service.filter_listings(categories=["see"])
    assert len(cats) == 1

    csv_text = service.filtered_csv(filtered)
    assert "Cafe Atlas" in csv_text
    assert "Louvre Gate" not in csv_text

    listing = service.get_listing("1111111111111111")
    assert listing is not None
    assert listing["name"] == "Cafe Atlas"


def test_sample_csv_fallback(tmp_path: Path) -> None:
    csv_path = tmp_path / "sample.csv"
    pd.DataFrame(_records()).to_csv(csv_path, index=False)
    service = DataService(
        sqlite_path=tmp_path / "missing.sqlite",
        sample_csv_path=csv_path,
    )
    service.load()
    assert service.source == "sample_csv"
    assert not service.is_empty
