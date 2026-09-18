"""Tests for static dashboard data generation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from travel_scraper.dashboard_export import (
    build_dashboard_data,
    load_listings_jsonl,
    sanitize,
)


def test_sanitize_rejects_nan_and_inf() -> None:
    assert sanitize(float("nan")) is None
    assert sanitize(float("inf")) is None
    assert sanitize({"latitude": float("nan"), "name": "X"}) == {
        "latitude": None,
        "name": "X",
    }


def test_build_dashboard_data(tmp_path: Path) -> None:
    listings = tmp_path / "travel_listings.jsonl"
    quality = tmp_path / "data_quality_report.json"
    out_dir = tmp_path / "docs_data"

    records = [
        {
            "id": "abc",
            "name": "Sample Place",
            "destination": "Paris",
            "country": "France",
            "category": "see",
            "latitude": 48.85,
            "longitude": 2.35,
        },
        {
            "id": "def",
            "name": "Cafe",
            "destination": "Paris",
            "country": "France",
            "category": "eat",
            "latitude": None,
            "longitude": None,
        },
    ]
    with listings.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")

    quality.write_text(
        json.dumps(
            {
                "final_records": 2,
                "raw_records": 2,
                "duplicates_removed": 0,
                "field_completeness": {"address": {"completeness_pct": 50.0}},
            }
        ),
        encoding="utf-8",
    )

    paths = build_dashboard_data(
        listings_path=listings,
        quality_path=quality,
        output_dir=out_dir,
    )

    listings_out = json.loads(paths["listings"].read_text(encoding="utf-8"))
    quality_out = json.loads(paths["quality"].read_text(encoding="utf-8"))

    assert len(listings_out) == 2
    assert listings_out[0]["destination"] == "Paris"
    assert quality_out["final_records"] == 2
    assert "field_completeness" in quality_out

    raw = paths["listings"].read_text(encoding="utf-8")
    assert "NaN" not in raw
    assert "Infinity" not in raw


def test_missing_listings_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_listings_jsonl(tmp_path / "missing.jsonl")
