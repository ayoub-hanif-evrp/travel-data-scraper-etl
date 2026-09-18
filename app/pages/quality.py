"""Data quality page."""

from __future__ import annotations

from nicegui import ui

from app.components.empty_state import empty_state
from app.components.metric_card import metric_card
from app.components.navigation import render_header
from app.data_service import DataService


def register_quality(service: DataService) -> None:
    @ui.page("/quality")
    def quality_page() -> None:
        render_header("/quality")
        service.load()

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            ui.label("Data Quality").classes("text-2xl font-semibold text-slate-800")

            if service.is_empty:
                empty_state()
                return

            q = service.quality_metrics()
            ui.label(
                f"Metrics source: {q.get('source')} · "
                f"Run: {q.get('run_timestamp') or 'n/a'}"
            ).classes("text-sm text-slate-500 -mt-4")

            with ui.row().classes("w-full gap-3 flex-wrap"):
                metric_card("Raw Records", q["raw_records"])
                metric_card("Valid Records", q["valid_records"])
                metric_card("Invalid Records", q["invalid_records"])
                metric_card("Duplicates Detected", q["duplicates_detected"])
                metric_card("Duplicates Removed", q["duplicates_removed"])
                metric_card("Final Records", q["final_records"])

            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.card().classes(
                    "flex-1 min-w-[280px] p-4 border border-slate-200 shadow-sm"
                ):
                    ui.label("Field completeness").classes(
                        "font-medium text-slate-700 mb-2"
                    )
                    completeness = q.get("field_completeness") or {}
                    for field, stats in completeness.items():
                        pct = stats.get("completeness_pct", 0)
                        with ui.row().classes("w-full items-center gap-3 mb-1"):
                            ui.label(field).classes("w-32 text-sm text-slate-600")
                            ui.linear_progress(value=float(pct) / 100.0).classes(
                                "flex-1"
                            )
                            ui.label(f"{pct}%").classes("w-14 text-sm text-slate-700")

                with ui.card().classes(
                    "flex-1 min-w-[280px] p-4 border border-slate-200 shadow-sm"
                ):
                    ui.label("Rejection reasons").classes(
                        "font-medium text-slate-700 mb-2"
                    )
                    reasons = q.get("rejection_reasons") or {}
                    if not reasons:
                        ui.label("No rejected records in the last ETL report.").classes(
                            "text-sm text-slate-500"
                        )
                    else:
                        for reason, count in sorted(
                            reasons.items(), key=lambda item: (-item[1], item[0])
                        ):
                            ui.label(f"{reason}: {count}").classes("text-sm text-slate-700")

            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.card().classes(
                    "flex-1 min-w-[280px] p-4 border border-slate-200 shadow-sm"
                ):
                    ui.label("By destination").classes("font-medium text-slate-700 mb-2")
                    for dest, count in (q.get("records_by_destination") or {}).items():
                        ui.label(f"{dest}: {count}").classes("text-sm text-slate-700")

                with ui.card().classes(
                    "flex-1 min-w-[280px] p-4 border border-slate-200 shadow-sm"
                ):
                    ui.label("By category").classes("font-medium text-slate-700 mb-2")
                    for cat, count in (q.get("records_by_category") or {}).items():
                        ui.label(f"{cat}: {count}").classes("text-sm text-slate-700")
