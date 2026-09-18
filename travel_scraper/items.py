"""Scrapy item definition for travel listings."""

from __future__ import annotations

import scrapy


class TravelListingItem(scrapy.Item):
    """Raw listing fields extracted from a destination page."""

    destination = scrapy.Field()
    country = scrapy.Field()
    category = scrapy.Field()
    subcategory = scrapy.Field()
    name = scrapy.Field()
    address = scrapy.Field()
    latitude = scrapy.Field()
    longitude = scrapy.Field()
    phone = scrapy.Field()
    email = scrapy.Field()
    website = scrapy.Field()
    opening_hours = scrapy.Field()
    price = scrapy.Field()
    description = scrapy.Field()
    source_url = scrapy.Field()
    source_listing_id = scrapy.Field()
    scraped_at = scrapy.Field()
