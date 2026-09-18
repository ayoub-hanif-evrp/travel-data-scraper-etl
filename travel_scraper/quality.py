"""Data quality report generation from ETL run statistics."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

IMPORTANT_FIELDS = (
    "address",
    "latitude",
    "longitude",
    "phone",
    "email",
    "website",
    "opening_hours",
    "price",
)


def _count_by(records: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for record in records:
        value = record.get(field) or "unknown"
        counter[str(value)] += 1
    return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))


def _completeness(records: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    total = len(records) or 1
    result: dict[str, dict[str, float | int]] = {}
    for field in IMPORTANT_FIELDS:
        present = sum(1 for r in records if r.get(field) not in (None, ""))
        # latitude/longitude: count rows with both for "coordinates"
        if field in {"latitude", "longitude"}:
            continue
        result[field] = {
            "present": present,
            "missing": len(records) - present,
            "completeness_pct": round(100.0 * present / total, 2),
        }
    coords_present = sum(
        1
        for r in records
        if r.get("latitude") is not None and r.get("longitude") is not None
    )
    result["coordinates"] = {
        "present": coords_present,
        "missing": len(records) - coords_present,
        "completeness_pct": round(100.0 * coords_present / total, 2),
    }
    return result


def build_quality_report(
    *,
    destinations: list[str],
    pages_requested: int,
    pages_ok: int,
    pages_failed: int,
    raw_count: int,
    valid_count: int,
    invalid_count: int,
    duplicates_detected: int,
    duplicates_removed: int,
    final_records: list[dict[str, Any]],
    rejection_reasons: dict[str, int],
    outputs: dict[str, str],
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    completeness = _completeness(final_records)
    coords_valid = completeness.get("coordinates", {}).get("present", 0)
    websites = sum(1 for r in final_records if r.get("website"))
    return {
        "run_timestamp": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "configured_destinations": destinations,
        "pages_requested": pages_requested,
        "pages_successfully_processed": pages_ok,
        "failed_pages": pages_failed,
        "raw_records": raw_count,
        "valid_records": valid_count,
        "invalid_records": invalid_count,
        "duplicates_detected": duplicates_detected,
        "duplicates_removed": duplicates_removed,
        "final_records": len(final_records),
        "records_by_destination": _count_by(final_records, "destination"),
        "records_by_category": _count_by(final_records, "category"),
        "field_completeness": completeness,
        "coordinate_validity": {
            "with_valid_coordinates": coords_valid,
            "without_coordinates": len(final_records) - int(coords_valid),
        },
        "url_validity": {
            "with_website": websites,
            "without_website": len(final_records) - websites,
        },
        "rejection_reasons": rejection_reasons,
        "generated_outputs": outputs,
        "warnings": warnings or [],
    }


def write_quality_reports(report: dict[str, Any], reports_dir: Path) -> tuple[Path, Path]:
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "data_quality_report.json"
    md_path = reports_dir / "data_quality_report.md"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return md_path, json_path


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Quality Report",
        "",
        f"**Run timestamp:** {report['run_timestamp']}",
        "",
        "## Crawl",
        "",
        f"- Configured destinations: {', '.join(report['configured_destinations'])}",
        f"- Pages requested: {report['pages_requested']}",
        f"- Pages successfully processed: {report['pages_successfully_processed']}",
        f"- Failed pages: {report['failed_pages']}",
        "",
        "## Pipeline counts",
        "",
        f"- Raw records: {report['raw_records']}",
        f"- Valid records: {report['valid_records']}",
        f"- Invalid records: {report['invalid_records']}",
        f"- Duplicates detected: {report['duplicates_detected']}",
        f"- Duplicates removed: {report['duplicates_removed']}",
        f"- Final records: {report['final_records']}",
        "",
        "## Records by destination",
        "",
    ]
    for key, value in report["records_by_destination"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Records by category", ""])
    for key, value in report["records_by_category"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Field completeness", ""])
    for field, stats in report["field_completeness"].items():
        lines.append(
            f"- {field}: {stats['present']} present "
            f"({stats['completeness_pct']}%), {stats['missing']} missing"
        )

    lines.extend(["", "## Rejection reasons", ""])
    if report["rejection_reasons"]:
        for reason, count in sorted(
            report["rejection_reasons"].items(), key=lambda item: (-item[1], item[0])
        ):
            lines.append(f"- {reason}: {count}")
    else:
        lines.append("- None")

    lines.extend(["", "## Generated outputs", ""])
    for label, path in report["generated_outputs"].items():
        lines.append(f"- {label}: `{path}`")

    if report.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        for warning in report["warnings"]:
            lines.append(f"- {warning}")

    lines.append("")
    return "\n".join(lines)
