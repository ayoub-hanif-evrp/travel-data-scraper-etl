"""Tests for Nova retrieval and AI configuration."""

from __future__ import annotations

import pytest
from server.ai import load_ai_settings
from server.retrieval import compact_listing, retrieve, score_listing, tokenize

SAMPLE = [
    {
        "id": "1",
        "name": "Eiffel Tower",
        "destination": "Paris",
        "country": "France",
        "category": "see",
        "address": "Champ de Mars",
        "description": "Iconic landmark",
        "website": "https://example.com",
        "latitude": 48.858,
        "longitude": 2.294,
    },
    {
        "id": "2",
        "name": "Le Comptoir",
        "destination": "Paris",
        "country": "France",
        "category": "eat",
        "address": "Left Bank",
        "description": "Bistro",
        "website": None,
        "latitude": 48.85,
        "longitude": 2.33,
    },
    {
        "id": "3",
        "name": "Senso-ji",
        "destination": "Tokyo",
        "country": "Japan",
        "category": "see",
        "address": "Asakusa",
        "description": "Temple",
        "website": "https://example.jp",
        "latitude": 35.71,
        "longitude": 139.79,
    },
]


def test_tokenize_and_score() -> None:
    tokens = set(tokenize("restaurants in Paris"))
    assert "paris" in tokens
    eat = score_listing("restaurants in Paris", SAMPLE[1], tokens, "eat")
    see = score_listing("restaurants in Paris", SAMPLE[0], tokens, "eat")
    assert eat > see


def test_retrieve_returns_trusted_matches() -> None:
    matches, stats = retrieve("places to eat in Paris", SAMPLE, limit=5)
    assert stats["total_places"] == 3
    assert matches
    assert matches[0]["category"] == "eat"
    compact = compact_listing(matches[0])
    assert compact["id"] == matches[0]["id"]
    assert "name" in compact


def test_load_ai_settings_missing_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("AI_PROVIDER", "groq")
    settings = load_ai_settings()
    assert settings.configured is False
    assert settings.provider == "groq"
    assert settings.model == "openai/gpt-oss-20b"


def test_load_ai_settings_groq(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_PROVIDER", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")
    monkeypatch.setenv("AI_MODEL", "openai/gpt-oss-20b")
    settings = load_ai_settings()
    assert settings.configured is True
    assert settings.provider == "groq"
    assert settings.api_key == "test-key-not-real"


def test_chat_validation_model() -> None:
    from pydantic import ValidationError
    from server.app import ChatRequest

    with pytest.raises(ValidationError):
        ChatRequest(message="")
    req = ChatRequest(message="Hello Paris", history=[{"role": "user", "content": "Hi"}])
    assert req.message.startswith("Hello")
