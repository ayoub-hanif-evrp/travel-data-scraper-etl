"""Pipeline explanation page (read-only)."""

from __future__ import annotations

from nicegui import ui
from travel_scraper import DEFAULT_DESTINATIONS

from app.components.navigation import render_header

STAGES = (
    ("Wikivoyage", "Configured English Wikivoyage destination pages only."),
    ("Scrapy", "Conservative crawl with robots.txt obedience and throttling."),
    ("Raw JSONL", "Source field values preserved before destructive transforms."),
    ("Cleaning", "Whitespace, URLs, phones, and coordinates normalized carefully."),
    ("Validation", "Required fields, ranges, and URL checks; rejects are retained."),
    ("Deduplication", "Deterministic identity keys; first occurrence kept."),
    ("SQLite / CSV / JSONL", "Analysis-ready structured exports with indexes."),
    ("NiceGUI", "Interactive exploration of the processed dataset."),
)


def register_pipeline() -> None:
    @ui.page("/pipeline")
    def pipeline_page() -> None:
        render_header("/pipeline")

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            ui.label("Pipeline").classes("text-2xl font-semibold text-slate-800")
            ui.label(
                "Architecture implemented by this demonstration project."
            ).classes("text-sm text-slate-500 -mt-4")

            with ui.card().classes("w-full p-5 border border-slate-200 shadow-sm"):
                for index, (title, blurb) in enumerate(STAGES):
                    with ui.row().classes("items-start gap-3"):
                        ui.label(f"{index + 1}").classes(
                            "w-7 h-7 rounded-full bg-slate-800 text-white "
                            "text-sm flex items-center justify-center shrink-0"
                        )
                        with ui.column().classes("gap-0"):
                            ui.label(title).classes("font-medium text-slate-800")
                            ui.label(blurb).classes("text-sm text-slate-600")
                    if index < len(STAGES) - 1:
                        ui.label("↓").classes("text-slate-400 ml-2 my-1")

            with ui.card().classes("w-full p-5 border border-slate-200 shadow-sm bg-slate-50"):
                ui.label("Crawl configuration (demo defaults)").classes(
                    "font-medium text-slate-800 mb-2"
                )
                ui.markdown(
                    f"""
- **Target destinations:** {", ".join(DEFAULT_DESTINATIONS)}
- **Crawl scope:** only the listed destination article pages (no link following)
- **Output formats:** raw JSONL → processed CSV / JSONL / SQLite + quality reports
- **Responsible settings:** `ROBOTSTXT_OBEY=True`, low concurrency, download delay,
  AutoThrottle, limited retries, informative `SCRAPER_USER_AGENT`
- **UI note:** this application does not start crawls — run
  `python scripts/run_demo.py` from the CLI
                    """.strip()
                )
