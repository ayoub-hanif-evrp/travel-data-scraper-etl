"""LLM provider clients for Nova (server-side only)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

SYSTEM_PROMPT = (
    "You are Nova, the travel discovery assistant inside Atlas. "
    "Answer using only the supplied Atlas dataset context. "
    "Never invent places, ratings, opening hours, prices, live availability, "
    "reviews, booking information, or facts absent from the context. "
    "When the requested information is not represented in the dataset, say so clearly. "
    "Keep responses concise and useful. Prefer named places from the provided context."
)


@dataclass(frozen=True)
class AISettings:
    provider: str
    model: str
    api_key: str | None
    configured: bool


def load_ai_settings() -> AISettings:
    provider = (os.getenv("AI_PROVIDER") or "groq").strip().lower()
    if provider == "openrouter":
        key = (os.getenv("OPENROUTER_API_KEY") or "").strip() or None
        model = (os.getenv("OPENROUTER_MODEL") or os.getenv("AI_MODEL") or "openai/gpt-oss-20b").strip()
    else:
        provider = "groq"
        key = (os.getenv("GROQ_API_KEY") or "").strip() or None
        model = (os.getenv("AI_MODEL") or "openai/gpt-oss-20b").strip()
    return AISettings(
        provider=provider,
        model=model,
        api_key=key,
        configured=bool(key),
    )


async def complete_chat(
    *,
    settings: AISettings,
    user_message: str,
    history: list[dict[str, str]],
    context: str,
) -> str:
    if not settings.configured or not settings.api_key:
        raise RuntimeError("AI is not configured")

    messages: list[dict[str, str]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "system",
            "content": f"Atlas dataset context:\n{context}",
        },
    ]
    for turn in history[-8:]:
        role = turn.get("role")
        content = turn.get("content")
        if role in {"user", "assistant"} and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content.strip()[:1500]})
    messages.append({"role": "user", "content": user_message.strip()[:1500]})

    if settings.provider == "openrouter":
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ayoub-hanif-evrp/travel-data-scraper-etl",
            "X-Title": "Atlas Nova",
        }
    else:
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.api_key}",
            "Content-Type": "application/json",
        }

    payload: dict[str, Any] = {
        "model": settings.model,
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 450,
    }

    async with httpx.AsyncClient(timeout=httpx.Timeout(45.0)) as client:
        response = await client.post(url, headers=headers, json=payload)

    if response.status_code == 401:
        raise PermissionError("AI provider rejected the API key")
    if response.status_code == 429:
        raise TimeoutError("AI provider rate limit reached")
    if response.status_code >= 500:
        raise RuntimeError("AI provider is temporarily unavailable")
    if response.status_code >= 400:
        raise RuntimeError("AI provider request failed")

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("AI provider returned an unexpected response") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("AI provider returned an empty answer")
    return content.strip()
