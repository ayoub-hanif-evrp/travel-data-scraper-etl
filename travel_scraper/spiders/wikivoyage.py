"""Wikivoyage destination spider — configured pages only, no link following."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from urllib.parse import quote

import scrapy

from travel_scraper import (
    DEFAULT_DESTINATIONS,
    DESTINATION_COUNTRY,
    WIKIVOYAGE_BASE,
)
from travel_scraper.items import TravelListingItem
from travel_scraper.parsing import parse_vcard

logger = logging.getLogger(__name__)


class WikivoyageSpider(scrapy.Spider):
    """Crawl a fixed list of English Wikivoyage destination pages."""

    name = "wikivoyage"
    allowed_domains = ["en.wikivoyage.org"]
    custom_settings = {
        "ROBOTSTXT_OBEY": True,
    }

    def __init__(
        self,
        destinations: str | None = None,
        limit: str | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        if destinations:
            self.destinations = [
                d.strip() for d in destinations.replace(";", ",").split(",") if d.strip()
            ]
        else:
            self.destinations = list(DEFAULT_DESTINATIONS)
        self.limit = int(limit) if limit else None
        self.pages_ok = 0
        self.pages_failed = 0

    async def start(self):
        for name in self.destinations:
            url = WIKIVOYAGE_BASE + quote(name.replace(" ", "_"))
            logger.info("Requesting destination: %s (%s)", name, url)
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.errback,
                meta={"destination": name, "dont_redirect": False},
                dont_filter=True,
            )

    def errback(self, failure: object) -> None:
        self.pages_failed += 1
        logger.error("Request failed: %s", failure)

    def parse(self, response: scrapy.http.Response):
        destination = response.meta.get("destination") or response.url.rsplit("/", 1)[-1]
        destination = destination.replace("_", " ")
        country = DESTINATION_COUNTRY.get(destination)
        scraped_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        canonical = response.css('link[rel="canonical"]::attr(href)').get() or response.url

        if response.status >= 400:
            self.pages_failed += 1
            logger.warning("HTTP %s for %s", response.status, response.url)
            return

        self.pages_ok += 1
        logger.info("Processing destination: %s", destination)

        count = 0
        for vcard in response.css("bdi.vcard"):
            record = parse_vcard(
                vcard,
                destination=destination,
                country=country,
                source_url=canonical,
                scraped_at=scraped_at,
            )
            if not record:
                continue
            count += 1
            yield TravelListingItem(**record)

        logger.info("Extracted %s listings from %s", count, destination)
        self.crawler.stats.set_value("pages_successfully_processed", self.pages_ok)
        self.crawler.stats.set_value("pages_failed", self.pages_failed)
        self.crawler.stats.set_value("configured_destinations", len(self.destinations))
