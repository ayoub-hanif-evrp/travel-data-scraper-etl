"""Travel Data Explorer entrypoint."""

from __future__ import annotations

import logging

from nicegui import ui

from app.config import APP_HOST, APP_NAME, APP_PORT
from app.data_service import DataService
from app.pages.listings import register_listings
from app.pages.overview import register_overview
from app.pages.pipeline import register_pipeline
from app.pages.quality import register_quality
from app.theme import apply_theme

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app() -> DataService:
    apply_theme()
    service = DataService()
    service.load()
    register_overview(service)
    register_listings(service)
    register_quality(service)
    register_pipeline()
    return service


def main() -> None:
    create_app()
    logger.info("Starting %s on http://%s:%s", APP_NAME, APP_HOST, APP_PORT)
    ui.run(
        host=APP_HOST,
        port=APP_PORT,
        title=APP_NAME,
        reload=False,
        show=False,
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
