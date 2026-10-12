"""Tavily Extract API client (Extract endpoint only; Search is not used)."""
import json
from typing import List

from .config import TAVILY_EXTRACT_URL
from .http_client import request, utc_now


class TavilyExtract:
    def __init__(self, api_key: str):
        self._key = api_key

    def extract(self, urls: List[str], depth: str) -> dict:
        """depth: 'basic' | 'advanced'. Returns status, timestamp and parsed body."""
        body = json.dumps({"urls": urls, "extract_depth": depth,
                           "format": "markdown", "include_images": False}).encode()
        retrieved_at = utc_now()
        r = request(TAVILY_EXTRACT_URL, "POST",
                    {"Authorization": f"Bearer {self._key}", "Content-Type": "application/json"},
                    body, timeout=120)
        try:
            data = json.loads(r.text)
        except ValueError:
            data = {"raw": r.text}
        return {"retrieved_at": retrieved_at, "http_status": r.status,
                "elapsed_s": round(r.elapsed_s, 2), "data": data}


def first_content(resp: dict) -> str:
    results = (resp.get("data") or {}).get("results") or []
    return results[0].get("raw_content", "") if results else ""
