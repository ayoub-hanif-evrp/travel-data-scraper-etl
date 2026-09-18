"""Application configuration from environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from travel_scraper import PROJECT_ROOT

load_dotenv()

APP_NAME = "Travel Data Explorer"
APP_SUBTITLE = "Structured travel data extraction, validation and ETL demonstration"

APP_HOST = os.getenv("APP_HOST", "127.0.0.1")
APP_PORT = int(os.getenv("APP_PORT", "8080"))

SQLITE_PATH = PROJECT_ROOT / "data" / "processed" / "travel_listings.sqlite"
SAMPLE_CSV_PATH = PROJECT_ROOT / "data" / "sample" / "travel_listings_sample.csv"
QUALITY_JSON_PATH = PROJECT_ROOT / "reports" / "data_quality_report.json"


def resolve_data_paths(
    *,
    sqlite_path: Path | None = None,
    sample_csv_path: Path | None = None,
    quality_json_path: Path | None = None,
) -> dict[str, Path]:
    return {
        "sqlite": sqlite_path or SQLITE_PATH,
        "sample_csv": sample_csv_path or SAMPLE_CSV_PATH,
        "quality_json": quality_json_path or QUALITY_JSON_PATH,
    }
