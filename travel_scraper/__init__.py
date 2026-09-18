"""Travel scraper package: Scrapy spider + ETL for Wikivoyage listings."""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent

DEFAULT_DESTINATIONS: tuple[str, ...] = (
    "Marrakech",
    "Fes",
    "Essaouira",
    "Chefchaouen",
    "Rabat",
)

DESTINATION_COUNTRY: dict[str, str] = {
    "Marrakech": "Morocco",
    "Fes": "Morocco",
    "Essaouira": "Morocco",
    "Chefchaouen": "Morocco",
    "Rabat": "Morocco",
}

SUPPORTED_CATEGORIES: frozenset[str] = frozenset(
    {"see", "do", "buy", "eat", "drink", "sleep"}
)

CATEGORY_ALIASES: dict[str, str] = {
    "see": "see",
    "do": "do",
    "buy": "buy",
    "eat": "eat",
    "drink": "drink",
    "sleep": "sleep",
    "go": "do",
    "view": "see",
    "listing": "see",
}

WIKIVOYAGE_BASE = "https://en.wikivoyage.org/wiki/"

DESCRIPTION_MAX_CHARS = 400
