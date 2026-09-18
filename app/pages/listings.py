"""Listings explorer page with filters, AG Grid, details, and CSV download."""

from __future__ import annotations

from nicegui import ui

from app.components.empty_state import empty_state
from app.components.navigation import render_header
from app.data_service import DataService
from app.formatting import display_value, format_coordinates

DETAIL_FIELDS = (
    ("name", "Name"),
    ("destination", "Destination"),
    ("category", "Category"),
    ("subcategory", "Subcategory"),
    ("address", "Address"),
    ("phone", "Phone"),
    ("email", "Email"),
    ("website", "Website"),
    ("opening_hours", "Opening hours"),
    ("price", "Price"),
    ("description", "Description"),
    ("source_url", "Source page"),
    ("scraped_at", "Scraped at"),
)


def register_listings(service: DataService) -> None:
    @ui.page("/listings")
    def listings_page() -> None:
        render_header("/listings")
        service.load()

        with ui.column().classes("w-full max-w-6xl mx-auto p-6 gap-4"):
            ui.label("Listings").classes("text-2xl font-semibold text-slate-800")

            if service.is_empty:
                empty_state()
                return

            state: dict = {
                "search": "",
                "destinations": [],
                "categories": [],
            }

            count_label = ui.label("").classes("text-sm text-slate-600")

            with ui.row().classes("w-full gap-3 flex-wrap items-end"):
                search_input = (
                    ui.input(label="Search", placeholder="Name, address, description…")
                    .classes("min-w-[220px] flex-1")
                    .props("clearable dense outlined")
                )
                dest_select = (
                    ui.select(
                        options=service.destinations(),
                        label="Destination",
                        multiple=True,
                    )
                    .classes("min-w-[180px]")
                    .props("dense outlined use-chips")
                )
                cat_select = (
                    ui.select(
                        options=service.categories(),
                        label="Category",
                        multiple=True,
                    )
                    .classes("min-w-[160px]")
                    .props("dense outlined use-chips")
                )
                reset_btn = ui.button("Reset filters").props("outline dense")
                download_btn = ui.button("Download filtered CSV").props("dense")

            grid = ui.aggrid(
                {
                    "columnDefs": [
                        {"field": "name", "headerName": "Name", "flex": 2},
                        {"field": "destination", "headerName": "Destination", "flex": 1},
                        {"field": "category", "headerName": "Category", "flex": 1},
                        {"field": "address", "headerName": "Address", "flex": 2},
                        {"field": "price", "headerName": "Price", "flex": 1},
                        {"field": "website", "headerName": "Website", "flex": 2},
                        {"field": "id", "hide": True},
                    ],
                    "rowData": [],
                    "rowSelection": "single",
                    "pagination": True,
                    "paginationPageSize": 25,
                    "defaultColDef": {
                        "sortable": True,
                        "resizable": True,
                        "filter": True,
                    },
                }
            ).classes("w-full h-[480px]")

            def refresh() -> None:
                filtered = service.filter_listings(
                    search=state["search"],
                    destinations=state["destinations"] or None,
                    categories=state["categories"] or None,
                )
                rows = []
                for _, row in filtered.iterrows():
                    rows.append(
                        {
                            "id": str(row.get("id", "")),
                            "name": display_value(row.get("name")) or "",
                            "destination": display_value(row.get("destination")) or "",
                            "category": display_value(row.get("category")) or "",
                            "address": display_value(row.get("address")) or "",
                            "price": display_value(row.get("price")) or "",
                            "website": display_value(row.get("website")) or "",
                        }
                    )
                grid.options["rowData"] = rows
                grid.update()
                count_label.set_text(f"{len(rows)} listing(s) match the current filters")

            def on_search(e) -> None:
                state["search"] = e.value or ""
                refresh()

            def on_dest(e) -> None:
                value = e.value or []
                state["destinations"] = value if isinstance(value, list) else [value]
                refresh()

            def on_cat(e) -> None:
                value = e.value or []
                state["categories"] = value if isinstance(value, list) else [value]
                refresh()

            def on_reset() -> None:
                state["search"] = ""
                state["destinations"] = []
                state["categories"] = []
                search_input.value = ""
                dest_select.value = []
                cat_select.value = []
                refresh()

            def on_download() -> None:
                filtered = service.filter_listings(
                    search=state["search"],
                    destinations=state["destinations"] or None,
                    categories=state["categories"] or None,
                )
                csv_text = service.filtered_csv(filtered)
                ui.download(csv_text.encode("utf-8"), "travel_listings_filtered.csv")

            async def on_row_selected(e) -> None:
                args = e.args
                if not args:
                    return
                # NiceGUI may pass selection payloads differently across versions
                selected = None
                if isinstance(args, dict):
                    selected = args.get("data") or (args.get("selectedData") or [None])[0]
                if not selected and isinstance(args, list) and args:
                    selected = args[0]
                if not isinstance(selected, dict):
                    return
                listing_id = selected.get("id")
                if not listing_id:
                    return
                record = service.get_listing(str(listing_id))
                if not record:
                    ui.notify("Listing not found", type="warning")
                    return
                _open_details(record)

            search_input.on_value_change(on_search)
            dest_select.on_value_change(on_dest)
            cat_select.on_value_change(on_cat)
            reset_btn.on_click(on_reset)
            download_btn.on_click(on_download)
            grid.on("rowSelected", on_row_selected)

            refresh()


def _open_details(record: dict) -> None:
    with ui.dialog() as dialog, ui.card().classes("w-[520px] max-w-[95vw] p-5 gap-2"):
        ui.label(display_value(record.get("name")) or "Listing").classes(
            "text-xl font-semibold text-slate-800"
        )
        coords = format_coordinates(record.get("latitude"), record.get("longitude"))
        for key, label in DETAIL_FIELDS:
            value = display_value(record.get(key))
            if not value:
                continue
            with ui.row().classes("w-full items-start gap-2"):
                ui.label(label).classes("w-32 text-sm text-slate-500 shrink-0")
                if key in {"website", "source_url"} and value.startswith("http"):
                    link_label = "Listing website" if key == "website" else "Wikivoyage source"
                    ui.link(link_label, value, new_tab=True).classes("text-sm")
                elif key == "email" and "@" in value:
                    ui.link(value, f"mailto:{value}").classes("text-sm")
                else:
                    ui.label(value).classes("text-sm text-slate-800")
        if coords:
            with ui.row().classes("w-full items-start gap-2"):
                ui.label("Coordinates").classes("w-32 text-sm text-slate-500 shrink-0")
                ui.label(coords).classes("text-sm text-slate-800")
        ui.button("Close", on_click=dialog.close).classes("mt-3").props("flat")
    dialog.open()
