"""Simple KPI metric card."""

from __future__ import annotations

from nicegui import ui


def metric_card(title: str, value: str | int | float) -> None:
    with ui.card().classes(
        "flex-1 min-w-[140px] p-4 shadow-sm border border-slate-200 bg-white"
    ):
        ui.label(title).classes("text-xs uppercase tracking-wide text-slate-500")
        ui.label(str(value)).classes("text-2xl font-semibold text-slate-800 mt-1")
