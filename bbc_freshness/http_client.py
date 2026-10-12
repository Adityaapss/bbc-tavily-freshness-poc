"""Tiny HTTP helper that never raises on HTTP errors."""
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import NamedTuple, Optional


class Response(NamedTuple):
    status: int          # 0 = network failure
    text: str
    elapsed_s: float


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def request(url: str, method: str = "GET", headers: Optional[dict] = None,
            body: Optional[bytes] = None, timeout: int = 60) -> Response:
    req = urllib.request.Request(url, data=body, method=method, headers=headers or {})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return Response(r.status, r.read().decode("utf-8", "replace"), time.time() - t0)
    except urllib.error.HTTPError as e:
        return Response(e.code, e.read().decode("utf-8", "replace"), time.time() - t0)
    except Exception as e:
        return Response(0, f"{type(e).__name__}: {e}", time.time() - t0)
