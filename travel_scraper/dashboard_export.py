"""Export processed pipeline outputs into static dashboard JSON files."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from travel_scraper import PROJECT_ROOT

DEFAULT_LISTINGS = PROJECT_ROOT / "data" / "processed" / "travel_listings.jsonl"
DEFAULT_QUALITY = PROJECT_ROOT / "reports" / "data_quality_report.json"
DEFAULT_OUT_DIR = PROJECT_ROOT / "docs" / "data"


def sanitize(value: Any) -> Any:
    """Convert values to JSON-safe primitives (no NaN/Infinity)."""
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return value
    if isinstance(value, dict):
        return {str(k): sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    return value


def load_listings_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Processed listings not found: {path}")
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(sanitize(json.loads(line)))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at {path}:{line_no}") from exc
    return records


def load_quality_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Quality report not found: {path}")
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Quality report must be a JSON object: {path}")
    return sanitize(data)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, allow_nan=False, indent=2)
        handle.write("\n")


def build_dashboard_data(
    *,
    listings_path: Path = DEFAULT_LISTINGS,
    quality_path: Path = DEFAULT_QUALITY,
    output_dir: Path = DEFAULT_OUT_DIR,
) -> dict[str, Path]:
    listings = load_listings_jsonl(listings_path)
    quality = load_quality_json(quality_path)

    listings_out = output_dir / "listings.json"
    quality_out = output_dir / "quality.json"
    write_json(listings_out, listings)
    write_json(quality_out, quality)
    return {"listings": listings_out, "quality": quality_out}
