"""Overview dashboard page."""

from __future__ import annotations

from nicegui import ui

from app.components.empty_state import empty_state
from app.components.metric_card import metric_card
from app.components.navigation import render_header
from app.data_service import DataService


def register_overview(service: DataService) -> None:
    @ui.page("/")
    def overview_page() -> None:
        render_header("/")
        service.load()
        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-6"):
            if service.is_empty:
                empty_state(
                    service.error
                    or "Run the scrape and ETL demo to populate the SQLite database."
                )
                return

            metrics = service.overview_metrics()
            etl = service.etl_summary()

            ui.label("Overview").classes("text-2xl font-semibold text-slate-800")
            source_note = (
                "Source: processed SQLite"
                if service.source == "sqlite"
                else "Source: sample CSV fallback"
            )
            ui.label(source_note).classes("text-sm text-slate-500 -mt-4")

            with ui.row().classes("w-full gap-3 flex-wrap"):
                metric_card("Total Listings", metrics["total_listings"])
                metric_card("Destinations", metrics["destinations"])
                metric_card("Categories", metrics["categories"])
                metric_card("With Coordinates", metrics["with_coordinates"])
                metric_card("With Website", metrics["with_website"])

            if etl:
                with ui.card().classes(
                    "w-full p-4 border border-slate-200 shadow-sm bg-slate-50"
                ):
                    ui.label("Latest ETL run").classes(
                        "text-sm font-medium text-slate-700"
                    )
                    ui.label(
                        f"Generated: {etl.get('run_timestamp') or 'n/a'} · "
                        f"Raw: {etl.get('raw_records')} · "
                        f"Final: {etl.get('final_records')} · "
                        f"Duplicates removed: {etl.get('duplicates_removed')} · "
                        f"Invalid: {etl.get('invalid_records')}"
                    ).classes("text-sm text-slate-600 mt-1")

            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.card().classes(
                    "flex-1 min-w-[280px] p-4 border border-slate-200 shadow-sm"
                ):
                    ui.label("Listings by Destination").classes(
                        "font-medium text-slate-700 mb-2"
                    )
                    dest = metrics["by_destination"]
                    ui.echart(
                        {
                            "tooltip": {"trigger": "axis"},
                            "xAxis": {
                                "type": "category",
                                "data": list(dest.keys()),
                                "axisLabel": {"rotate": 20},
                            },
                            "yAxis": {"type": "value"},
                            "series": [
                                {
                                    "type": "bar",
                                    "data": list(dest.values()),
                                    "itemStyle": {"color": "#334155"},
                                }
                            ],
                        }
                    ).classes("w-full h-64")

                with ui.card().classes(
                    "flex-1 min-w-[280px] p-4 border border-slate-200 shadow-sm"
                ):
                    ui.label("Listings by Category").classes(
                        "font-medium text-slate-700 mb-2"
                    )
                    cats = metrics["by_category"]
                    ui.echart(
                        {
                            "tooltip": {"trigger": "item"},
                            "series": [
                                {
                                    "type": "pie",
                                    "radius": ["35%", "65%"],
                                    "data": [
                                        {"name": k, "value": v} for k, v in cats.items()
                                    ],
                                }
                            ],
                        }
                    ).classes("w-full h-64")

            with ui.card().classes("w-full p-4 border border-slate-200 shadow-sm"):
                ui.label("Geocoded listings").classes("font-medium text-slate-700 mb-2")
                points = metrics["map_points"]
                if not points:
                    ui.label(
                        "No records with valid coordinates in the current dataset."
                    ).classes("text-sm text-slate-500")
                else:
                    lats = [p["lat"] for p in points]
                    lons = [p["lon"] for p in points]
                    center = (sum(lats) / len(lats), sum(lons) / len(lons))
                    leaflet = ui.leaflet(center=center, zoom=7).classes(
                        "w-full h-96 rounded border border-slate-200"
                    )
                    for point in points:
                        marker = leaflet.marker(latlng=(point["lat"], point["lon"]))
                        popup = (
                            f"{point['name']}<br/>"
                            f"{point['destination']} · {point['category']}"
                        )
                        marker.run_method("bindPopup", popup)
