"""Atlas FastAPI application: static frontend + Nova chat API."""

from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from travel_scraper import PROJECT_ROOT

from server.ai import complete_chat, load_ai_settings
from server.retrieval import compact_listing, context_for_llm, retrieve

load_dotenv(PROJECT_ROOT / ".env")

DOCS_DIR = PROJECT_ROOT / "docs"
LISTINGS_PATH = DOCS_DIR / "data" / "listings.json"

app = FastAPI(title="Atlas", docs_url=None, redoc_url=None)
_listings_cache: list[dict[str, Any]] | None = None
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)
RATE_LIMIT = 15
RATE_WINDOW_SEC = 60


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1400)
    history: list[dict[str, str]] = Field(default_factory=list)


def load_listings() -> list[dict[str, Any]]:
    global _listings_cache
    if _listings_cache is not None:
        return _listings_cache
    if not LISTINGS_PATH.is_file():
        raise FileNotFoundError(f"Missing listings data: {LISTINGS_PATH}")
    payload = json.loads(LISTINGS_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("listings.json must be a JSON array")
    _listings_cache = payload
    return _listings_cache


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def enforce_rate_limit(request: Request) -> None:
    ip = client_ip(request)
    now = time.monotonic()
    bucket = _rate_buckets[ip]
    while bucket and now - bucket[0] > RATE_WINDOW_SEC:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Too many requests. Please wait a moment.")
    bucket.append(now)


@app.get("/api/health")
def health() -> dict[str, Any]:
    settings = load_ai_settings()
    listings_ok = LISTINGS_PATH.is_file()
    return {
        "ok": True,
        "ai_configured": settings.configured,
        "provider": settings.provider if settings.configured else None,
        "model": settings.model if settings.configured else None,
        "listings_available": listings_ok,
    }


@app.post("/api/chat")
async def chat(payload: ChatRequest, request: Request) -> dict[str, Any]:
    enforce_rate_limit(request)
    settings = load_ai_settings()
    if not settings.configured:
        raise HTTPException(
            status_code=503,
            detail="AI assistant unavailable. Configure GROQ_API_KEY (or OPENROUTER_API_KEY) in .env.",
        )

    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message is required.")

    history = payload.history[-8:]
    try:
        listings = load_listings()
    except (OSError, ValueError, FileNotFoundError):
        raise HTTPException(status_code=503, detail="Place dataset is unavailable.") from None

    matches, stats = retrieve(message, listings, limit=12)
    context = context_for_llm(matches, stats)

    try:
        answer = await complete_chat(
            settings=settings,
            user_message=message,
            history=history,
            context=context,
        )
    except PermissionError:
        raise HTTPException(status_code=502, detail="AI provider rejected the API key.") from None
    except TimeoutError:
        raise HTTPException(status_code=429, detail="AI provider rate limit reached. Try again soon.") from None
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    except Exception:
        raise HTTPException(status_code=502, detail="Nova could not reach the AI provider.") from None

    return {
        "answer": answer,
        "matches": [compact_listing(row) for row in matches if row.get("id")],
    }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(DOCS_DIR / "index.html")


if (DOCS_DIR / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=DOCS_DIR / "assets"), name="assets")
if (DOCS_DIR / "data").is_dir():
    app.mount("/data", StaticFiles(directory=DOCS_DIR / "data"), name="data")
if (DOCS_DIR / "images").is_dir():
    app.mount("/images", StaticFiles(directory=DOCS_DIR / "images"), name="images")
