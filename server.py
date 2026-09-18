#!/usr/bin/env python3
"""Run the Atlas explorer with Nova AI support."""

from __future__ import annotations

import os

import uvicorn
from dotenv import load_dotenv
from travel_scraper import PROJECT_ROOT

load_dotenv(PROJECT_ROOT / ".env")


def main() -> None:
    host = os.getenv("ATLAS_HOST", "127.0.0.1")
    port = int(os.getenv("ATLAS_PORT", "8080"))
    uvicorn.run("server.app:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
