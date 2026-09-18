"""Formatting helpers for UI display."""

from __future__ import annotations

from typing import Any


def display_value(value: Any) -> str | None:
    """Return a display string, or None when the value should be omitted."""
    if value is None:
        return None
    if isinstance(value, float):
        return f"{value:.6g}"
    text = str(value).strip()
    return text or None


def format_coordinates(lat: Any, lon: Any) -> str | None:
    if lat is None or lon is None:
        return None
    try:
        return f"{float(lat):.5f}, {float(lon):.5f}"
    except (TypeError, ValueError):
        return None
