"""Empty-state panel when no dataset is available."""

from __future__ import annotations

from nicegui import ui


def empty_state(message: str | None = None) -> None:
    text = message or (
        "No travel listings are available yet. "
        "Generate data with the demo command below."
    )
    with ui.card().classes(
        "w-full max-w-xl mx-auto mt-16 p-8 border border-slate-200 shadow-sm bg-white"
    ):
        ui.label("No dataset loaded").classes("text-xl font-semibold text-slate-800")
        ui.label(text).classes("text-slate-600 mt-2")
        ui.code("python scripts/run_demo.py").classes("mt-4 w-full")
        ui.label(
            "Then restart the application with: python -m app.main"
        ).classes("text-sm text-slate-500 mt-3")
