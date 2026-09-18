"""Lightweight lexical retrieval over Atlas place listings."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

TOKEN_RE = re.compile(r"[a-z0-9]+", re.I)

CATEGORY_ALIASES = {
    "restaurant": "eat",
    "restaurants": "eat",
    "food": "eat",
    "eat": "eat",
    "dining": "eat",
    "cafe": "drink",
    "cafes": "drink",
    "bar": "drink",
    "bars": "drink",
    "drink": "drink",
    "nightlife": "drink",
    "hotel": "sleep",
    "hotels": "sleep",
    "stay": "sleep",
    "stays": "sleep",
    "sleep": "sleep",
    "hostel": "sleep",
    "see": "see",
    "sight": "see",
    "sights": "see",
    "attraction": "see",
    "attractions": "see",
    "visit": "see",
    "do": "do",
    "activity": "do",
    "activities": "do",
    "things": "do",
    "buy": "buy",
    "shop": "buy",
    "shopping": "buy",
}


def tokenize(text: str) -> list[str]:
    return [t.casefold() for t in TOKEN_RE.findall(text or "")]


def detect_category(tokens: set[str]) -> str | None:
    for token in tokens:
        if token in CATEGORY_ALIASES:
            return CATEGORY_ALIASES[token]
    return None


def score_listing(query: str, listing: dict[str, Any], tokens: set[str], category: str | None) -> float:
    score = 0.0
    fields = {
        "name": 4.0,
        "destination": 3.5,
        "country": 3.0,
        "category": 2.5,
        "address": 1.5,
        "description": 1.0,
        "subcategory": 1.2,
    }
    q = query.casefold()
    for field, weight in fields.items():
        value = str(listing.get(field) or "").casefold()
        if not value:
            continue
        if q and q in value:
            score += weight * 2.5
        field_tokens = set(tokenize(value))
        overlap = tokens & field_tokens
        score += weight * len(overlap)
    if category and str(listing.get("category") or "").casefold() == category:
        score += 5.0
    if listing.get("website") and ("website" in tokens or "websites" in tokens):
        score += 2.0
    return score


def aggregate_stats(listings: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "total_places": len(listings),
        "countries": sorted({str(r.get("country")) for r in listings if r.get("country")}),
        "destinations": sorted({str(r.get("destination")) for r in listings if r.get("destination")}),
        "categories": dict(Counter(str(r.get("category")) for r in listings if r.get("category"))),
        "by_destination": dict(
            Counter(str(r.get("destination")) for r in listings if r.get("destination"))
        ),
    }


def retrieve(
    query: str,
    listings: list[dict[str, Any]],
    *,
    limit: int = 12,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return top matching listings and compact aggregate stats."""
    tokens = set(tokenize(query))
    category = detect_category(tokens)
    scored: list[tuple[float, dict[str, Any]]] = []
    for listing in listings:
        points = score_listing(query, listing, tokens, category)
        if points > 0:
            scored.append((points, listing))
    scored.sort(key=lambda item: (-item[0], str(item[1].get("name") or "")))
    matches = [item[1] for item in scored[:limit]]
    stats = aggregate_stats(listings)
    return matches, stats


def compact_listing(listing: dict[str, Any]) -> dict[str, Any]:
    """Trusted match payload for the frontend (never LLM-invented IDs)."""
    return {
        "id": listing.get("id"),
        "name": listing.get("name"),
        "destination": listing.get("destination"),
        "country": listing.get("country"),
        "category": listing.get("category"),
        "address": listing.get("address"),
        "latitude": listing.get("latitude"),
        "longitude": listing.get("longitude"),
    }


def context_for_llm(matches: list[dict[str, Any]], stats: dict[str, Any]) -> str:
    lines = [
        f"Dataset places: {stats['total_places']}",
        f"Countries: {', '.join(stats['countries'])}",
        f"Destinations: {', '.join(stats['destinations'])}",
        f"Category counts: {stats['categories']}",
        "Relevant places:",
    ]
    for row in matches:
        lines.append(
            " | ".join(
                [
                    f"id={row.get('id')}",
                    f"name={row.get('name')}",
                    f"category={row.get('category')}",
                    f"destination={row.get('destination')}",
                    f"country={row.get('country')}",
                    f"address={row.get('address') or ''}",
                    f"price={row.get('price') or ''}",
                    f"website={'yes' if row.get('website') else 'no'}",
                    f"description={(row.get('description') or '')[:180]}",
                ]
            )
        )
    return "\n".join(lines)
