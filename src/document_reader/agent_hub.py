"""Client helpers for the RoadScript orchestrator."""

from __future__ import annotations

import logging
import os
from typing import Any

import json
import urllib.parse
import urllib.request
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

HUB_URL = os.getenv("ROADSCRIPT_HUB_URL", "http://127.0.0.1:9000").rstrip("/")
AGENT_NAME = os.getenv("AGENT_NAME", "DocumentReader")
AGENT_BASE_URL = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:9002")


def register_agent(capabilities: list[str] | None = None) -> None:
    payload = {
        "name": AGENT_NAME,
        "base_url": AGENT_BASE_URL,
        "capabilities": capabilities
        or ["document-processing", "ocr", "indot-sheet", "measurements"],
        "metadata": {},
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{HUB_URL}/registry/register",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
        logger.info("Registered %s with orchestrator", AGENT_NAME)
    except Exception as exc:  # pragma: no cover
        logger.warning("Unable to register with orchestrator: %s", exc)


def publish_knowledge(item: dict[str, Any]) -> None:
    try:
        data = json.dumps(item).encode("utf-8")
        req = urllib.request.Request(
            f"{HUB_URL}/knowledge/ingest",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as exc:  # pragma: no cover
        logger.warning("Unable to publish knowledge: %s", exc)


def fetch_knowledge(
    *,
    source: str | None = None,
    topic: str | None = None,
    tag: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    params = {"limit": str(limit)}
    if source:
        params["source"] = source
    if topic:
        params["topic"] = topic
    if tag:
        params["tag"] = tag
    query = urllib.parse.urlencode(params)
    url = f"{HUB_URL}/knowledge/query?{query}"
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))
