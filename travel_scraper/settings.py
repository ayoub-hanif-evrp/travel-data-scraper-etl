"""Conservative Scrapy settings for Wikivoyage demonstration crawls."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "travel_scraper"

SPIDER_MODULES = ["travel_scraper.spiders"]
NEWSPIDER_MODULE = "travel_scraper.spiders"

_DEFAULT_UA = (
    "TravelDataPortfolio/1.0 "
    "(+https://github.com/YOUR_USERNAME/travel-data-scraper-etl)"
)
USER_AGENT = os.getenv("SCRAPER_USER_AGENT", _DEFAULT_UA)

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = False
DOWNLOAD_DELAY_JITTER = 0.5

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.5
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5

RETRY_ENABLED = True
RETRY_TIMES = 2
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

COOKIES_ENABLED = False
TELNETCONSOLE_ENABLED = False
DOWNLOAD_TIMEOUT = 30

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en",
}

ITEM_PIPELINES = {
    "travel_scraper.pipelines.RawJsonlPipeline": 300,
}

FEEDS = {}

LOG_LEVEL = "INFO"

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_OUTPUT_PATH = str(_PROJECT_ROOT / "data" / "raw" / "listings_raw.jsonl")

# Do not download media
MEDIA_ALLOW_REDIRECTS = False
IMAGES_STORE = None
FILES_STORE = None
