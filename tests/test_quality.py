"""Quality report tests."""

from __future__ import annotations

import json
from pathlib import Path

from travel_scraper.quality import build_quality_report, write_quality_reports


def test_quality_report_generation(tmp_path: Path) -> None:
    records = [
        {
            "destination": "Rabat",
            "category": "see",
            "name": "A",
            "address": "x",
            "latitude": 34.0,
            "longitude": -6.8,
            "website": "https://example.com",
            "phone": None,
            "email": None,
            "opening_hours": None,
            "price": None,
        }
    ]
    report = build_quality_report(
        destinations=["Rabat"],
        pages_requested=1,
        pages_ok=1,
        pages_failed=0,
        raw_count=1,
        valid_count=1,
        invalid_count=0,
        duplicates_detected=0,
        duplicates_removed=0,
        final_records=records,
        rejection_reasons={},
        outputs={"csv": "data/processed/travel_listings.csv"},
    )
    assert report["final_records"] == 1
    assert report["records_by_destination"]["Rabat"] == 1
    assert report["field_completeness"]["address"]["present"] == 1

    md_path, json_path = write_quality_reports(report, tmp_path)
    assert md_path.exists()
    loaded = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded["raw_records"] == 1
    assert "Data Quality Report" in md_path.read_text(encoding="utf-8")
