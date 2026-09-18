"""Empty-state panel when no dataset is available."""

from __future__ import annotations

from nicegui import ui


def empty_state(message: str | None = None) -> None:
    text = message or (
        "No travel listings are available yet. "
        "Generate data with the demo command below."
    )
    with ui.element("div").classes("tde-empty"):
        ui.label("No dataset loaded").classes("tde-page-title text-xl")
        ui.label(text).classes("text-slate-600 mt-3")
        ui.code("python scripts/run_demo.py").classes("mt-5 inline-block text-left")
        ui.label("Then restart with: python -m app.main").classes(
            "text-sm text-slate-500 mt-3"
        )
