"""Pipeline explanation page (read-only)."""

from __future__ import annotations

from nicegui import ui
from travel_scraper import DEFAULT_DESTINATIONS

from app.components.navigation import render_header
from app.theme import PAGE_SHELL, SECTION_CARD, page_heading

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

        with ui.column().classes(PAGE_SHELL):
            page_heading(
                "Pipeline",
                "Architecture implemented by this demonstration project.",
            )

            with ui.element("div").classes(SECTION_CARD):
                for index, (title, blurb) in enumerate(STAGES):
                    with ui.row().classes("items-start gap-3 py-2"):
                        with ui.element("div").classes("tde-step-num"):
                            ui.label(str(index + 1)).classes("text-white text-sm")
                        with ui.column().classes("gap-0"):
                            ui.label(title).classes("font-semibold text-slate-900")
                            ui.label(blurb).classes("text-sm text-slate-600")
                    if index < len(STAGES) - 1:
                        ui.label("↓").classes("text-teal-600/50 ml-3 my-0.5")

            with ui.element("div").classes(SECTION_CARD + " tde-etl-banner"):
                ui.label("Crawl configuration (demo defaults)").classes(
                    "tde-section-title"
                )
                dest_lines = ", ".join(
                    f"{d.name} ({d.country})" for d in DEFAULT_DESTINATIONS
                )
                ui.markdown(
                    f"""
- **Target destinations:** {dest_lines}
- **Crawl scope:** only the listed destination article pages (no link following)
- **Output formats:** raw JSONL → processed CSV / JSONL / SQLite + quality reports
- **Responsible settings:** `ROBOTSTXT_OBEY=True`, low concurrency, download delay,
  AutoThrottle, limited retries, informative `SCRAPER_USER_AGENT`
- **UI note:** this application does not start crawls — run
  `python scripts/run_demo.py` from the CLI
                    """.strip()
                )
