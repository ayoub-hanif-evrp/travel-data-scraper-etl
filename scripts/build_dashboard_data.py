#!/usr/bin/env python3
"""Build static dashboard JSON from existing processed pipeline outputs."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from travel_scraper.dashboard_export import (
    DEFAULT_LISTINGS,
    DEFAULT_OUT_DIR,
    DEFAULT_QUALITY,
    build_dashboard_data,
)

logger = logging.getLogger("build_dashboard_data")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build docs/data JSON for the static Data Delivery Dashboard.",
    )
    parser.add_argument("--listings", type=Path, default=DEFAULT_LISTINGS)
    parser.add_argument("--quality", type=Path, default=DEFAULT_QUALITY)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    args = parse_args(argv)
    try:
        paths = build_dashboard_data(
            listings_path=args.listings,
            quality_path=args.quality,
            output_dir=args.output_dir,
        )
    except (OSError, ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        logger.error("%s", exc)
        return 1
    logger.info("Wrote listings to %s", paths["listings"])
    logger.info("Wrote quality report to %s", paths["quality"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
