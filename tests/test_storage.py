"""Storage export tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from travel_scraper.storage import write_csv, write_jsonl, write_sqlite


def _sample() -> list[dict]:
    return [
        {
            "id": "abc123def4567890",
            "destination": "Essaouira",
            "country": "Morocco",
            "category": "see",
            "subcategory": None,
            "name": "Ramparts",
            "address": "Harbour",
            "latitude": 31.51,
            "longitude": -9.77,
            "phone": None,
            "email": None,
            "website": "https://example.com",
            "opening_hours": None,
            "price": None,
            "description": "Sea walls",
            "source_url": "https://en.wikivoyage.org/wiki/Essaouira",
            "source_listing_id": "Ramparts",
            "scraped_at": "2026-01-01T00:00:00+00:00",
        }
    ]


def test_sqlite_creation_and_indexes(tmp_path: Path) -> None:
    db = tmp_path / "travel_listings.sqlite"
    write_sqlite(_sample(), db)
    with sqlite3.connect(db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM travel_listings").fetchone()[0]
        assert count == 1
        indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list('travel_listings')").fetchall()
        }
        assert "idx_listings_destination" in indexes
        assert "idx_listings_category" in indexes
        assert "idx_listings_name" in indexes
        row = conn.execute(
            "SELECT name FROM travel_listings WHERE destination = ?",
            ("Essaouira",),
        ).fetchone()
        assert row[0] == "Ramparts"


def test_csv_and_jsonl(tmp_path: Path) -> None:
    csv_path = tmp_path / "out.csv"
    jsonl_path = tmp_path / "out.jsonl"
    write_csv(_sample(), csv_path)
    write_jsonl(_sample(), jsonl_path)
    assert "Ramparts" in csv_path.read_text(encoding="utf-8")
    line = jsonl_path.read_text(encoding="utf-8").strip()
    assert json.loads(line)["name"] == "Ramparts"
