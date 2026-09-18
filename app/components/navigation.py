"""Persistent top navigation."""

from __future__ import annotations

from nicegui import ui

from app.config import APP_NAME, APP_SUBTITLE

NAV_ITEMS = (
    ("/", "Overview"),
    ("/listings", "Listings"),
    ("/quality", "Data Quality"),
    ("/pipeline", "Pipeline"),
)


def render_header(active: str) -> None:
    with ui.header().classes("items-center px-6 py-3 bg-slate-800 text-white"):
        with ui.column().classes("gap-0 mr-8"):
            ui.label(APP_NAME).classes("text-lg font-semibold tracking-tight")
            ui.label(APP_SUBTITLE).classes("text-xs text-slate-300")
        with ui.row().classes("items-center gap-1 flex-wrap"):
            for path, label in NAV_ITEMS:
                classes = "px-3 py-1 rounded text-sm"
                if path == active:
                    classes += " bg-slate-600 font-medium"
                else:
                    classes += " hover:bg-slate-700"
                ui.link(label, path).classes(classes + " text-white no-underline")
