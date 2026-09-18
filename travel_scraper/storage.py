"""Structured storage: SQLite, CSV, and JSONL exports."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

LISTING_COLUMNS: list[str] = [
    "id",
    "destination",
    "country",
    "category",
    "subcategory",
    "name",
    "address",
    "latitude",
    "longitude",
    "phone",
    "email",
    "website",
    "opening_hours",
    "price",
    "description",
    "source_url",
    "source_listing_id",
    "scraped_at",
]

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS travel_listings (
    id TEXT PRIMARY KEY,
    destination TEXT NOT NULL,
    country TEXT,
    category TEXT NOT NULL,
    subcategory TEXT,
    name TEXT NOT NULL,
    address TEXT,
    latitude REAL,
    longitude REAL,
    phone TEXT,
    email TEXT,
    website TEXT,
    opening_hours TEXT,
    price TEXT,
    description TEXT,
    source_url TEXT NOT NULL,
    source_listing_id TEXT,
    scraped_at TEXT NOT NULL
)
"""

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_listings_destination ON travel_listings(destination)",
    "CREATE INDEX IF NOT EXISTS idx_listings_category ON travel_listings(category)",
    "CREATE INDEX IF NOT EXISTS idx_listings_name ON travel_listings(name)",
    "CREATE INDEX IF NOT EXISTS idx_listings_source_url ON travel_listings(source_url)",
]


def records_to_dataframe(records: list[dict[str, Any]]) -> pd.DataFrame:
    if not records:
        return pd.DataFrame(columns=LISTING_COLUMNS)
    df = pd.DataFrame(records)
    for col in LISTING_COLUMNS:
        if col not in df.columns:
            df[col] = None
    return df[LISTING_COLUMNS]


def write_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            row = {col: record.get(col) for col in LISTING_COLUMNS}
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    records_to_dataframe(records).to_csv(path, index=False, encoding="utf-8")


def write_rejected_jsonl(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_sqlite(records: list[dict[str, Any]], path: Path) -> None:
    """Create (or replace) a deterministic SQLite database of listings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    with sqlite3.connect(path) as conn:
        conn.execute(CREATE_TABLE_SQL)
        for statement in INDEX_SQL:
            conn.execute(statement)
        if records:
            rows = [
                tuple(record.get(col) for col in LISTING_COLUMNS) for record in records
            ]
            placeholders = ", ".join("?" for _ in LISTING_COLUMNS)
            columns = ", ".join(LISTING_COLUMNS)
            conn.executemany(
                f"INSERT INTO travel_listings ({columns}) VALUES ({placeholders})",
                rows,
            )
        conn.commit()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
