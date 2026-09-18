"""Data quality page."""

from __future__ import annotations

from nicegui import ui

from app.components.empty_state import empty_state
from app.components.metric_card import metric_card
from app.components.navigation import render_header
from app.data_service import DataService
from app.theme import PAGE_SHELL, PANEL_CARD, page_heading


def register_quality(service: DataService) -> None:
    @ui.page("/quality")
    def quality_page() -> None:
        render_header("/quality")
        service.load()

        with ui.column().classes(PAGE_SHELL):
            if service.is_empty:
                page_heading("Data Quality")
                empty_state()
                return

            q = service.quality_metrics()
            page_heading(
                "Data Quality",
                f"Metrics source: {q.get('source')} · Run: {q.get('run_timestamp') or 'n/a'}",
            )

            with ui.row().classes("w-full gap-3 flex-wrap"):
                metric_card("Raw Records", q["raw_records"])
                metric_card("Valid Records", q["valid_records"])
                metric_card("Invalid Records", q["invalid_records"])
                metric_card("Duplicates Detected", q["duplicates_detected"])
                metric_card("Duplicates Removed", q["duplicates_removed"])
                metric_card("Final Records", q["final_records"])

            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.element("div").classes(PANEL_CARD):
                    ui.label("Field completeness").classes("tde-section-title")
                    completeness = q.get("field_completeness") or {}
                    for field, stats in completeness.items():
                        pct = stats.get("completeness_pct", 0)
                        with ui.row().classes("w-full items-center gap-3 mb-2"):
                            ui.label(field).classes("w-32 text-sm text-slate-600")
                            ui.linear_progress(
                                value=float(pct) / 100.0, color="teal"
                            ).classes("flex-1")
                            ui.label(f"{pct}%").classes(
                                "w-14 text-sm font-medium text-slate-700"
                            )

                with ui.element("div").classes(PANEL_CARD):
                    ui.label("Rejection reasons").classes("tde-section-title")
                    reasons = q.get("rejection_reasons") or {}
                    if not reasons:
                        ui.label(
                            "No rejected records in the last ETL report."
                        ).classes("text-sm text-slate-500")
                    else:
                        for reason, count in sorted(
                            reasons.items(), key=lambda item: (-item[1], item[0])
                        ):
                            ui.label(f"{reason}: {count}").classes(
                                "text-sm text-slate-700 mb-1"
                            )

            with ui.row().classes("w-full gap-4 flex-wrap"):
                for title, key in (
                    ("By destination", "records_by_destination"),
                    ("By country", "records_by_country"),
                    ("By category", "records_by_category"),
                ):
                    with ui.element("div").classes(PANEL_CARD):
                        ui.label(title).classes("tde-section-title")
                        for name, count in (q.get(key) or {}).items():
                            with ui.row().classes(
                                "w-full justify-between text-sm py-1 "
                                "border-b border-slate-100"
                            ):
                                ui.label(str(name)).classes("text-slate-700")
                                ui.label(str(count)).classes(
                                    "font-semibold text-teal-800"
                                )
