"""Deterministic deduplication and stable record identifiers.

Matching strategy (documented for portfolio reviewers)
------------------------------------------------------
Build a normalized identity key from, in priority order:

1. destination (lowercased)
2. name (lowercased, collapsed whitespace)
3. coordinates when both latitude and longitude are present
   (rounded to 5 decimal places ≈ 1 m precision)
4. otherwise address when available (lowercased)
5. otherwise category as a weak tie-breaker

Records sharing the same key are duplicates. The first occurrence is kept
(stable, deterministic order of the input list). A project-owned ``id`` is a
SHA-256 hex digest truncated to 16 characters over the identity key material.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

_WS = re.compile(r"\s+", re.UNICODE)


def _norm_text(value: str | None) -> str:
    if not value:
        return ""
    return _WS.sub(" ", value).strip().lower()


def identity_key(record: dict[str, Any]) -> str:
    destination = _norm_text(record.get("destination"))
    name = _norm_text(record.get("name"))
    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is not None and lon is not None:
        geo = f"{round(float(lat), 5)}|{round(float(lon), 5)}"
    else:
        address = _norm_text(record.get("address"))
        geo = address or _norm_text(record.get("category"))
    return f"{destination}|{name}|{geo}"


def make_record_id(record: dict[str, Any]) -> str:
    key = identity_key(record)
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


@dataclass
class DeduplicationResult:
    records: list[dict[str, Any]] = field(default_factory=list)
    duplicates_detected: int = 0
    duplicates_removed: int = 0

    @property
    def final_count(self) -> int:
        return len(self.records)


def deduplicate_records(records: list[dict[str, Any]]) -> DeduplicationResult:
    """Keep first occurrence per identity key; assign stable ids."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    duplicates_detected = 0

    for record in records:
        key = identity_key(record)
        if key in seen:
            duplicates_detected += 1
            continue
        seen.add(key)
        enriched = dict(record)
        enriched["id"] = make_record_id(enriched)
        unique.append(enriched)

    return DeduplicationResult(
        records=unique,
        duplicates_detected=duplicates_detected,
        duplicates_removed=duplicates_detected,
    )
