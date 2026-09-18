"""Overview dashboard page."""

from __future__ import annotations

from nicegui import ui

from app.components.empty_state import empty_state
from app.components.metric_card import metric_card
from app.components.navigation import render_header
from app.data_service import DataService
from app.theme import CHART_COLORS, PAGE_SHELL, PANEL_CARD, SECTION_CARD, page_heading


def register_overview(service: DataService) -> None:
    @ui.page("/")
    def overview_page() -> None:
        render_header("/")
        service.load()
        with ui.column().classes(PAGE_SHELL):
            if service.is_empty:
                empty_state(
                    service.error
                    or "Run the scrape and ETL demo to populate the SQLite database."
                )
                return

            metrics = service.overview_metrics()
            etl = service.etl_summary()
            source_note = (
                "Source: processed SQLite"
                if service.source == "sqlite"
                else "Source: sample CSV fallback"
            )
            page_heading("Overview", source_note)

            with ui.row().classes("w-full gap-3 flex-wrap"):
                metric_card("Total Listings", metrics["total_listings"])
                metric_card("Destinations", metrics["destinations"])
                metric_card("Countries", metrics["countries"])
                metric_card("Categories", metrics["categories"])
                metric_card("With Coordinates", metrics["with_coordinates"])
                metric_card("With Website", metrics["with_website"])

            if etl:
                with ui.element("div").classes("tde-etl-banner w-full"):
                    ui.label("Latest ETL run").classes(
                        "text-sm font-semibold text-teal-900"
                    )
                    ui.label(
                        f"Generated: {etl.get('run_timestamp') or 'n/a'} · "
                        f"Raw: {etl.get('raw_records')} · "
                        f"Final: {etl.get('final_records')} · "
                        f"Duplicates removed: {etl.get('duplicates_removed')} · "
                        f"Invalid: {etl.get('invalid_records')}"
                    ).classes("text-sm text-slate-600 mt-1")

            with ui.row().classes("w-full gap-4 flex-wrap"):
                with ui.element("div").classes(PANEL_CARD):
                    ui.label("Listings by Destination").classes("tde-section-title")
                    dest = metrics["by_destination"]
                    ui.echart(
                        {
                            "color": CHART_COLORS,
                            "tooltip": {"trigger": "axis"},
                            "grid": {
                                "left": 40,
                                "right": 16,
                                "top": 24,
                                "bottom": 48,
                            },
                            "xAxis": {
                                "type": "category",
                                "data": list(dest.keys()),
                                "axisLabel": {"rotate": 20, "color": "#64748b"},
                                "axisLine": {"lineStyle": {"color": "#cbd5e1"}},
                            },
                            "yAxis": {
                                "type": "value",
                                "splitLine": {"lineStyle": {"color": "#e2e8f0"}},
                                "axisLabel": {"color": "#64748b"},
                            },
                            "series": [
                                {
                                    "type": "bar",
                                    "data": list(dest.values()),
                                    "barWidth": "48%",
                                    "itemStyle": {
                                        "borderRadius": [6, 6, 0, 0],
                                        "color": {
                                            "type": "linear",
                                            "x": 0,
                                            "y": 0,
                                            "x2": 0,
                                            "y2": 1,
                                            "colorStops": [
                                                {"offset": 0, "color": "#0d9488"},
                                                {"offset": 1, "color": "#115e59"},
                                            ],
                                        },
                                    },
                                }
                            ],
                        }
                    ).classes("w-full h-64")

                with ui.element("div").classes(PANEL_CARD):
                    ui.label("Listings by Category").classes("tde-section-title")
                    cats = metrics["by_category"]
                    ui.echart(
                        {
                            "color": CHART_COLORS,
                            "tooltip": {"trigger": "item"},
                            "legend": {
                                "bottom": 0,
                                "textStyle": {"color": "#64748b"},
                            },
                            "series": [
                                {
                                    "type": "pie",
                                    "radius": ["42%", "68%"],
                                    "center": ["50%", "45%"],
                                    "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                                    "label": {"color": "#334155"},
                                    "data": [
                                        {"name": k, "value": v} for k, v in cats.items()
                                    ],
                                }
                            ],
                        }
                    ).classes("w-full h-64")

            with ui.element("div").classes(SECTION_CARD):
                ui.label("Geocoded listings").classes("tde-section-title")
                points = metrics["map_points"]
                if not points:
                    ui.label(
                        "No records with valid coordinates in the current dataset."
                    ).classes("text-sm text-slate-500")
                else:
                    lats = [p["lat"] for p in points]
                    lons = [p["lon"] for p in points]
                    center = (sum(lats) / len(lats), sum(lons) / len(lons))
                    leaflet = ui.leaflet(center=center, zoom=2).classes(
                        "w-full h-96 rounded-xl overflow-hidden border border-slate-200"
                    )
                    for point in points:
                        marker = leaflet.marker(latlng=(point["lat"], point["lon"]))
                        country = point.get("country") or ""
                        place = (
                            f"{point['destination']}, {country}"
                            if country
                            else point["destination"]
                        )
                        popup = (
                            f"<strong>{point['name']}</strong><br/>"
                            f"{place} · {point['category']}"
                        )
                        marker.run_method("bindPopup", popup)
