"""Data access layer for the NiceGUI explorer (SQLite preferred, CSV fallback)."""

from __future__ import annotations

import io
import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
from travel_scraper.storage import LISTING_COLUMNS

from app.config import QUALITY_JSON_PATH, SAMPLE_CSV_PATH, SQLITE_PATH

logger = logging.getLogger(__name__)


@dataclass
class DataService:
    """Load and query travel listings without UI coupling."""

    sqlite_path: Path = field(default_factory=lambda: SQLITE_PATH)
    sample_csv_path: Path = field(default_factory=lambda: SAMPLE_CSV_PATH)
    quality_json_path: Path = field(default_factory=lambda: QUALITY_JSON_PATH)
    _df: pd.DataFrame | None = field(default=None, init=False, repr=False)
    source: str = field(default="none", init=False)
    error: str | None = field(default=None, init=False)

    def load(self) -> pd.DataFrame:
        self.error = None
        if self.sqlite_path.exists():
            try:
                with sqlite3.connect(self.sqlite_path) as conn:
                    df = pd.read_sql_query("SELECT * FROM travel_listings", conn)
                self._df = _normalize_frame(df)
                self.source = "sqlite"
                return self._df
            except (sqlite3.Error, pd.errors.DatabaseError, ValueError) as exc:
                logger.exception("SQLite read failed: %s", exc)
                self.error = f"SQLite read failed: {exc}"

        if self.sample_csv_path.exists():
            try:
                df = pd.read_csv(self.sample_csv_path)
                self._df = _normalize_frame(df)
                self.source = "sample_csv"
                return self._df
            except (OSError, pd.errors.ParserError, ValueError) as exc:
                logger.exception("Sample CSV read failed: %s", exc)
                self.error = f"Sample CSV read failed: {exc}"

        self._df = pd.DataFrame(columns=LISTING_COLUMNS)
        self.source = "none"
        return self._df

    @property
    def df(self) -> pd.DataFrame:
        if self._df is None:
            return self.load()
        return self._df

    @property
    def is_empty(self) -> bool:
        return self.df.empty

    def destinations(self) -> list[str]:
        if self.is_empty or "destination" not in self.df.columns:
            return []
        return sorted(self.df["destination"].dropna().astype(str).unique().tolist())

    def countries(self) -> list[str]:
        if self.is_empty or "country" not in self.df.columns:
            return []
        return sorted(self.df["country"].dropna().astype(str).unique().tolist())

    def categories(self) -> list[str]:
        if self.is_empty or "category" not in self.df.columns:
            return []
        return sorted(self.df["category"].dropna().astype(str).unique().tolist())

    def filter_listings(
        self,
        *,
        search: str | None = None,
        destinations: list[str] | None = None,
        countries: list[str] | None = None,
        categories: list[str] | None = None,
    ) -> pd.DataFrame:
        frame = self.df
        if frame.empty:
            return frame

        mask = pd.Series(True, index=frame.index)
        if destinations:
            mask &= frame["destination"].isin(destinations)
        if countries and "country" in frame.columns:
            mask &= frame["country"].isin(countries)
        if categories:
            mask &= frame["category"].isin(categories)
        if search:
            query = search.strip().lower()
            if query:
                searchable = (
                    frame.get("name", pd.Series("", index=frame.index))
                    .fillna("")
                    .astype(str)
                    .str.lower()
                )
                for col in ("address", "description", "destination", "country", "category"):
                    if col in frame.columns:
                        searchable = (
                            searchable + " " + frame[col].fillna("").astype(str).str.lower()
                        )
                mask &= searchable.str.contains(query, regex=False)
        return frame.loc[mask].copy()

    def get_listing(self, listing_id: str) -> dict[str, Any] | None:
        if self.is_empty or "id" not in self.df.columns:
            return None
        matches = self.df.loc[self.df["id"].astype(str) == str(listing_id)]
        if matches.empty:
            return None
        return _row_to_dict(matches.iloc[0])

    def overview_metrics(self) -> dict[str, Any]:
        frame = self.df
        if frame.empty:
            return {
                "total_listings": 0,
                "destinations": 0,
                "countries": 0,
                "categories": 0,
                "with_coordinates": 0,
                "with_website": 0,
                "by_destination": {},
                "by_country": {},
                "by_category": {},
                "map_points": [],
            }
        with_coords = frame.dropna(subset=["latitude", "longitude"])
        map_points = [
            {
                "id": str(row.get("id", "")),
                "name": str(row.get("name", "")),
                "destination": str(row.get("destination", "")),
                "country": str(row.get("country") or ""),
                "category": str(row.get("category", "")),
                "lat": float(row["latitude"]),
                "lon": float(row["longitude"]),
            }
            for _, row in with_coords.iterrows()
            if _valid_coords(row.get("latitude"), row.get("longitude"))
        ]
        countries_series = (
            frame["country"].dropna() if "country" in frame.columns else pd.Series(dtype=object)
        )
        return {
            "total_listings": int(len(frame)),
            "destinations": int(frame["destination"].nunique()),
            "countries": int(countries_series.nunique()) if not countries_series.empty else 0,
            "categories": int(frame["category"].nunique()),
            "with_coordinates": len(map_points),
            "with_website": int(frame["website"].notna().sum())
            if "website" in frame.columns
            else 0,
            "by_destination": frame["destination"].value_counts().to_dict(),
            "by_country": countries_series.value_counts().to_dict()
            if not countries_series.empty
            else {},
            "by_category": frame["category"].value_counts().to_dict(),
            "map_points": map_points,
        }

    def filtered_csv(self, filtered: pd.DataFrame) -> str:
        buffer = io.StringIO()
        export = filtered.copy()
        for col in LISTING_COLUMNS:
            if col not in export.columns:
                export[col] = None
        export[LISTING_COLUMNS].to_csv(buffer, index=False, encoding="utf-8")
        return buffer.getvalue()

    def quality_metrics(self) -> dict[str, Any]:
        report = self.load_quality_report()
        if report:
            completeness = report.get("field_completeness") or {}
            return {
                "raw_records": report.get("raw_records", 0),
                "valid_records": report.get("valid_records", 0),
                "invalid_records": report.get("invalid_records", 0),
                "duplicates_detected": report.get("duplicates_detected", 0),
                "duplicates_removed": report.get("duplicates_removed", 0),
                "final_records": report.get("final_records", len(self.df)),
                "field_completeness": completeness,
                "records_by_destination": report.get("records_by_destination", {}),
                "records_by_country": report.get("records_by_country", {}),
                "records_by_category": report.get("records_by_category", {}),
                "rejection_reasons": report.get("rejection_reasons", {}),
                "run_timestamp": report.get("run_timestamp"),
                "source": "quality_report",
            }
        # Recompute from loaded dataset when report is missing
        metrics = self.overview_metrics()
        total = metrics["total_listings"] or 1
        completeness: dict[str, dict[str, float | int]] = {}
        for field_name in (
            "address",
            "phone",
            "email",
            "website",
            "opening_hours",
            "price",
        ):
            if field_name not in self.df.columns:
                present = 0
            else:
                present = int(self.df[field_name].notna().sum())
            completeness[field_name] = {
                "present": present,
                "missing": metrics["total_listings"] - present,
                "completeness_pct": round(100.0 * present / total, 2),
            }
        completeness["coordinates"] = {
            "present": metrics["with_coordinates"],
            "missing": metrics["total_listings"] - metrics["with_coordinates"],
            "completeness_pct": round(100.0 * metrics["with_coordinates"] / total, 2),
        }
        return {
            "raw_records": metrics["total_listings"],
            "valid_records": metrics["total_listings"],
            "invalid_records": 0,
            "duplicates_detected": 0,
            "duplicates_removed": 0,
            "final_records": metrics["total_listings"],
            "field_completeness": completeness,
            "records_by_destination": metrics["by_destination"],
            "records_by_country": metrics["by_country"],
            "records_by_category": metrics["by_category"],
            "rejection_reasons": {},
            "run_timestamp": None,
            "source": "dataset",
        }

    def load_quality_report(self) -> dict[str, Any] | None:
        path = self.quality_json_path
        if not path.exists():
            return None
        try:
            with path.open(encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Malformed quality JSON: %s", exc)
            return None

    def etl_summary(self) -> dict[str, Any]:
        report = self.load_quality_report()
        if not report:
            return {}
        return {
            "run_timestamp": report.get("run_timestamp"),
            "raw_records": report.get("raw_records"),
            "final_records": report.get("final_records"),
            "duplicates_removed": report.get("duplicates_removed"),
            "invalid_records": report.get("invalid_records"),
        }


def _normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    for col in LISTING_COLUMNS:
        if col not in df.columns:
            df[col] = None
    for col in ("latitude", "longitude"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def _row_to_dict(row: pd.Series) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            result[str(key)] = None
        else:
            result[str(key)] = value.item() if hasattr(value, "item") else value
    return result


def _valid_coords(lat: Any, lon: Any) -> bool:
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return False
    return -90 <= lat_f <= 90 and -180 <= lon_f <= 180


def dataframe_from_csv_bytes(content: str) -> pd.DataFrame:
    """Utility for tests — parse a CSV string into a DataFrame."""
    return pd.read_csv(io.StringIO(content))
