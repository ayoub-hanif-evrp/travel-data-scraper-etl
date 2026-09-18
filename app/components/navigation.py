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
    with ui.header().classes("tde-header items-center justify-between px-6 py-4 gap-4"):
        with ui.row().classes("items-center gap-8 flex-wrap"):
            with ui.column().classes("gap-0"):
                ui.label(APP_NAME).classes("tde-brand text-xl text-white")
                ui.label(APP_SUBTITLE).classes("text-xs text-teal-100/80 max-w-md")
            with ui.row().classes("items-center gap-1 flex-wrap"):
                for path, label in NAV_ITEMS:
                    classes = "tde-nav-link"
                    if path == active:
                        classes += " active"
                    ui.link(label, path).classes(classes)
