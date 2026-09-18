"""Wikivoyage destination spider — configured pages only, no link following."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from urllib.parse import quote

import scrapy

from travel_scraper import (
    DEFAULT_DESTINATIONS,
    WIKIVOYAGE_BASE,
    Destination,
    destinations_to_payload,
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
        destinations_json: str | None = None,
        limit: str | None = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.destination_specs = self._parse_destination_specs(destinations, destinations_json)
        self.limit = int(limit) if limit else None
        self.pages_ok = 0
        self.pages_failed = 0

    @staticmethod
    def _parse_destination_specs(
        destinations: str | None,
        destinations_json: str | None,
    ) -> list[Destination]:
        if destinations_json:
            payload = json.loads(destinations_json)
            if not isinstance(payload, list) or not payload:
                raise ValueError("destinations_json must be a non-empty JSON array")
            specs: list[Destination] = []
            for index, item in enumerate(payload):
                if not isinstance(item, dict):
                    raise ValueError(f"destinations_json[{index}] must be an object")
                name = item.get("name")
                country = item.get("country")
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(f"destinations_json[{index}] requires name")
                if not isinstance(country, str) or not country.strip():
                    raise ValueError(
                        f"Destination '{name}' requires explicit country in destinations_json"
                    )
                specs.append(Destination(name=name.strip(), country=country.strip()))
            return specs

        if destinations:
            # Legacy name-only spider arg: country left unknown unless caller used destinations_json.
            names = [d.strip() for d in destinations.replace(";", ",").split(",") if d.strip()]
            return [Destination(name=name, country="") for name in names]

        return list(DEFAULT_DESTINATIONS)

    @property
    def destinations(self) -> list[str]:
        return [d.name for d in self.destination_specs]

    async def start(self):
        for spec in self.destination_specs:
            url = WIKIVOYAGE_BASE + quote(spec.name.replace(" ", "_"))
            country = spec.country.strip() or None
            logger.info(
                "Requesting destination: %s (%s)%s",
                spec.name,
                url,
                f" [{country}]" if country else " [country unknown]",
            )
            yield scrapy.Request(
                url,
                callback=self.parse,
                errback=self.errback,
                meta={
                    "destination": spec.name,
                    "country": country,
                    "dont_redirect": False,
                },
                dont_filter=True,
            )

    def errback(self, failure: object) -> None:
        self.pages_failed += 1
        logger.error("Request failed: %s", failure)

    def parse(self, response: scrapy.http.Response):
        destination = response.meta.get("destination") or response.url.rsplit("/", 1)[-1]
        destination = destination.replace("_", " ")
        country = response.meta.get("country")
        scraped_at = datetime.now(UTC).replace(microsecond=0).isoformat()
        canonical = response.css('link[rel="canonical"]::attr(href)').get() or response.url

        if response.status >= 400:
            self.pages_failed += 1
            logger.warning("HTTP %s for %s", response.status, response.url)
            return

        self.pages_ok += 1
        logger.info(
            "Processing destination: %s%s",
            destination,
            f" ({country})" if country else "",
        )

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
        self.crawler.stats.set_value("configured_destinations", len(self.destination_specs))
        self.crawler.stats.set_value(
            "destination_payload",
            destinations_to_payload(self.destination_specs),
        )
