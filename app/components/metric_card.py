"""KPI metric card."""

from __future__ import annotations

from nicegui import ui


def metric_card(title: str, value: str | int | float) -> None:
    with ui.element("div").classes("tde-metric"):
        ui.label(title).classes("tde-metric-label")
        ui.label(str(value)).classes("tde-metric-value")
