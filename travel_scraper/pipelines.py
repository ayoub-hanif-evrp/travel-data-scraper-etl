"""Scrapy pipelines — write raw crawl output only."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from itemadapter import ItemAdapter

logger = logging.getLogger(__name__)


class RawJsonlPipeline:
    """Append each yielded item to a JSONL file as raw source values."""

    def __init__(self, output_path: str, crawler: Any | None = None) -> None:
        self.output_path = Path(output_path)
        self.crawler = crawler
        self._file: Any = None
        self.count = 0

    @classmethod
    def from_crawler(cls, crawler: Any) -> RawJsonlPipeline:
        path = crawler.settings.get(
            "RAW_OUTPUT_PATH",
            "data/raw/listings_raw.jsonl",
        )
        return cls(path, crawler=crawler)

    def open_spider(self, spider: Any = None) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("w", encoding="utf-8")
        self.count = 0
        logger.info("Writing raw listings to %s", self.output_path)

    def close_spider(self, spider: Any = None) -> None:
        if self._file is not None:
            self._file.close()
        logger.info("Raw records written: %s", self.count)
        if self.crawler is not None:
            self.crawler.stats.set_value("raw_records_written", self.count)

    def process_item(self, item: Any, spider: Any = None) -> Any:
        adapter = ItemAdapter(item)
        record = dict(adapter)
        assert self._file is not None
        self._file.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.count += 1
        spider_obj = spider if spider is not None else getattr(self.crawler, "spider", None)
        limit = getattr(spider_obj, "limit", None) if spider_obj is not None else None
        if limit is not None and self.count >= int(limit) and self.crawler is not None:
            self.crawler.engine.close_spider(spider_obj, reason="limit_reached")
        return item
