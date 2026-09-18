#!/usr/bin/env python3
"""Orchestrate a conservative Wikivoyage crawl + ETL demonstration."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from scrapy import signals
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from travel_scraper import (
    DEFAULT_DESTINATIONS_FILE,
    PROJECT_ROOT,
    Destination,
    destinations_to_payload,
    load_default_destinations,
    load_destinations_file,
    lookup_destination,
)
from travel_scraper.dashboard_export import build_dashboard_data
from travel_scraper.etl import run_etl
from travel_scraper.spiders.wikivoyage import WikivoyageSpider

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("run_demo")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Travel Data Scraping & ETL Pipeline demo.",
    )
    parser.add_argument(
        "--destinations-file",
        type=Path,
        default=None,
        help=(
            "JSON file of {name, country} pairs "
            f"(default: {DEFAULT_DESTINATIONS_FILE.name})"
        ),
    )
    parser.add_argument(
        "--destinations",
        nargs="+",
        default=None,
        help="Optional destination page titles (countries resolved from config when known)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional cap on raw listings written during the crawl",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data",
        help="Base data directory (raw/processed/sample live under this path)",
    )
    parser.add_argument(
        "--skip-crawl",
        action="store_true",
        help="Skip Scrapy and re-run ETL against existing raw JSONL",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=80,
        help="Maximum rows in the repository sample export",
    )
    return parser.parse_args(argv)


def resolve_destination_specs(args: argparse.Namespace) -> list[Destination]:
    """Build destination/country pairs from file and/or CLI names."""
    if args.destinations_file is not None:
        base = load_destinations_file(args.destinations_file)
    else:
        base = load_default_destinations()

    if not args.destinations:
        return base

    registry = {d.name.casefold(): d for d in base}
    # Also allow resolving against the repository demo file when a custom file is used.
    if args.destinations_file is not None:
        for demo in load_default_destinations():
            registry.setdefault(demo.name.casefold(), demo)

    specs: list[Destination] = []
    for name in args.destinations:
        known = registry.get(name.strip().casefold()) or lookup_destination(name)
        if known is None:
            raise SystemExit(
                f"Destination '{name}' has no country metadata. "
                "Add it to a destinations JSON file with an explicit country field."
            )
        specs.append(Destination(name=known.name, country=known.country))
    return specs


def run_crawl(destinations: list[Destination], limit: int | None, raw_path: Path) -> dict[str, int]:
    names = [d.name for d in destinations]
    logger.info("Starting crawl for destinations: %s", ", ".join(names))
    settings = get_project_settings()
    settings.set("RAW_OUTPUT_PATH", str(raw_path), priority="cmdline")
    process = CrawlerProcess(settings)
    crawl_stats = {
        "pages_requested": len(destinations),
        "pages_ok": 0,
        "pages_failed": 0,
    }

    def _on_spider_closed(spider: WikivoyageSpider) -> None:
        crawl_stats["pages_ok"] = int(getattr(spider, "pages_ok", 0))
        crawl_stats["pages_failed"] = int(getattr(spider, "pages_failed", 0))

    crawler = process.create_crawler(WikivoyageSpider)
    crawler.signals.connect(_on_spider_closed, signal=signals.spider_closed)
    process.crawl(
        crawler,
        destinations_json=json.dumps(destinations_to_payload(destinations)),
        limit=str(limit) if limit is not None else None,
    )
    process.start()
    return crawl_stats


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir: Path = args.output_dir
    raw_dir = output_dir / "raw"
    processed_dir = output_dir / "processed"
    sample_dir = output_dir / "sample"
    reports_dir = PROJECT_ROOT / "reports"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / "listings_raw.jsonl"
    crawl_meta_path = raw_dir / "crawl_meta.json"

    destination_specs = resolve_destination_specs(args)
    destinations = [d.name for d in destination_specs]

    if args.skip_crawl:
        logger.info("Skipping crawl; using existing raw data at %s", raw_path)
        if not raw_path.exists():
            logger.error("Raw file not found: %s", raw_path)
            return 1
        crawl_stats = {
            "pages_requested": len(destinations),
            "pages_ok": 0,
            "pages_failed": 0,
        }
        if crawl_meta_path.exists():
            try:
                meta = json.loads(crawl_meta_path.read_text(encoding="utf-8-sig"))
                crawl_stats.update(
                    {
                        "pages_requested": int(
                            meta.get("pages_requested", crawl_stats["pages_requested"])
                        ),
                        "pages_ok": int(meta.get("pages_ok", 0)),
                        "pages_failed": int(meta.get("pages_failed", 0)),
                    }
                )
                if meta.get("destinations"):
                    destinations = list(meta["destinations"])
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.warning("Could not read crawl meta: %s", exc)
    else:
        crawl_stats = run_crawl(destination_specs, args.limit, raw_path)
        crawl_meta_path.write_text(
            json.dumps(
                {
                    "destinations": destinations,
                    "destination_specs": destinations_to_payload(destination_specs),
                    **crawl_stats,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    logger.info("Raw records written / available for ETL")
    result = run_etl(
        raw_path=raw_path,
        processed_dir=processed_dir,
        reports_dir=reports_dir,
        sample_dir=sample_dir,
        destinations=destinations,
        pages_requested=crawl_stats["pages_requested"],
        pages_ok=crawl_stats["pages_ok"],
        pages_failed=crawl_stats["pages_failed"],
        sample_size=args.sample_size,
    )

    try:
        dash_paths = build_dashboard_data()
        logger.info("Dashboard data written: %s", dash_paths["listings"])
    except (OSError, ValueError, FileNotFoundError) as exc:
        logger.warning("Could not refresh dashboard data: %s", exc)
        dash_paths = None

    print()
    print("=== Travel Data Pipeline demo complete ===")
    print(
        "Destinations:     "
        + ", ".join(f"{d.name} ({d.country})" for d in destination_specs)
    )
    print(f"Pages OK / fail:  {crawl_stats['pages_ok']} / {crawl_stats['pages_failed']}")
    print(f"Raw records:      {result['raw_count']}")
    print(f"Valid:            {result['valid_count']}")
    print(f"Invalid:          {result['invalid_count']}")
    print(f"Duplicates removed: {result['duplicates_removed']}")
    print(f"Final records:    {result['final_count']}")
    print(f"CSV:              {result['outputs']['csv']}")
    print(f"JSONL:            {result['outputs']['jsonl']}")
    print(f"SQLite:           {result['outputs']['sqlite']}")
    print(f"Quality report:   {result['outputs']['quality_md']}")
    if dash_paths:
        print(f"Dashboard data:   {dash_paths['listings']}")
    print()
    print("View Atlas with AI:     python server.py")
    print("Static explorer only:   python -m http.server 8080 -d docs")
    logger.info("Demo complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
