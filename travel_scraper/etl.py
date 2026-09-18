"""ETL orchestration callable independently of Scrapy."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from travel_scraper import PROJECT_ROOT
from travel_scraper.cleaning import clean_records
from travel_scraper.deduplication import deduplicate_records
from travel_scraper.quality import build_quality_report, write_quality_reports
from travel_scraper.storage import (
    read_jsonl,
    write_csv,
    write_jsonl,
    write_rejected_jsonl,
    write_sqlite,
)
from travel_scraper.validation import validate_records

logger = logging.getLogger(__name__)


def run_etl(
    *,
    raw_path: Path,
    processed_dir: Path,
    reports_dir: Path,
    sample_dir: Path,
    destinations: list[str],
    pages_requested: int = 0,
    pages_ok: int = 0,
    pages_failed: int = 0,
    sample_size: int = 80,
) -> dict[str, Any]:
    """Run cleaning → validation → deduplication → storage → quality reports."""
    logger.info("Starting ETL")
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    raw_records = read_jsonl(raw_path)
    raw_count = len(raw_records)
    logger.info("Loaded %s raw records from %s", raw_count, raw_path)

    cleaned = clean_records(raw_records)
    logger.info("Validating records")
    validation = validate_records(cleaned)

    rejected_path = processed_dir / "rejected_records.jsonl"
    if validation.invalid:
        write_rejected_jsonl(validation.invalid, rejected_path)
    elif rejected_path.exists():
        rejected_path.unlink()

    logger.info(
        "Validation complete: %s valid, %s invalid",
        validation.valid_count,
        validation.invalid_count,
    )

    dedup = deduplicate_records(validation.valid)
    logger.info(
        "Duplicates removed: %s (final unique: %s)",
        dedup.duplicates_removed,
        dedup.final_count,
    )

    csv_path = processed_dir / "travel_listings.csv"
    jsonl_path = processed_dir / "travel_listings.jsonl"
    sqlite_path = processed_dir / "travel_listings.sqlite"

    write_csv(dedup.records, csv_path)
    write_jsonl(dedup.records, jsonl_path)
    write_sqlite(dedup.records, sqlite_path)
    logger.info("SQLite written: %s", sqlite_path)

    # Representative sample across destinations/categories
    sample = _build_sample(dedup.records, sample_size)
    sample_csv = sample_dir / "travel_listings_sample.csv"
    sample_jsonl = sample_dir / "travel_listings_sample.jsonl"
    write_csv(sample, sample_csv)
    write_jsonl(sample, sample_jsonl)

    outputs = {
        "csv": _rel(csv_path),
        "jsonl": _rel(jsonl_path),
        "sqlite": _rel(sqlite_path),
        "sample_csv": _rel(sample_csv),
        "sample_jsonl": _rel(sample_jsonl),
    }
    if validation.invalid:
        outputs["rejected"] = _rel(rejected_path)

    report = build_quality_report(
        destinations=destinations,
        pages_requested=pages_requested,
        pages_ok=pages_ok,
        pages_failed=pages_failed,
        raw_count=raw_count,
        valid_count=validation.valid_count,
        invalid_count=validation.invalid_count,
        duplicates_detected=dedup.duplicates_detected,
        duplicates_removed=dedup.duplicates_removed,
        final_records=dedup.records,
        rejection_reasons=validation.rejection_reasons,
        outputs=outputs,
    )
    md_path, json_report_path = write_quality_reports(report, reports_dir)
    outputs["quality_md"] = _rel(md_path)
    outputs["quality_json"] = _rel(json_report_path)
    # Refresh report with relative quality paths
    report["generated_outputs"] = outputs
    write_quality_reports(report, reports_dir)
    logger.info("Reports generated")

    return {
        "raw_count": raw_count,
        "valid_count": validation.valid_count,
        "invalid_count": validation.invalid_count,
        "duplicates_removed": dedup.duplicates_removed,
        "final_count": dedup.final_count,
        "outputs": {**outputs, "csv": str(csv_path), "jsonl": str(jsonl_path), "sqlite": str(sqlite_path), "quality_md": str(md_path)},
        "report": report,
    }


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _build_sample(records: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    if len(records) <= sample_size:
        return list(records)
    # Round-robin by destination then category for diversity
    buckets: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        key = f"{record.get('destination')}|{record.get('category')}"
        buckets.setdefault(key, []).append(record)
    sample: list[dict[str, Any]] = []
    while len(sample) < sample_size and buckets:
        empty_keys: list[str] = []
        for key in list(buckets.keys()):
            if len(sample) >= sample_size:
                break
            bucket = buckets[key]
            if not bucket:
                empty_keys.append(key)
                continue
            sample.append(bucket.pop(0))
            if not bucket:
                empty_keys.append(key)
        for key in empty_keys:
            buckets.pop(key, None)
    return sample
