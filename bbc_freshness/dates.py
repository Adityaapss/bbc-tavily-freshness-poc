"""Best-effort publish/modified timestamps from a BBC article page."""
import re
from typing import Dict, Optional


def _json_field(html: str, *names: str) -> Optional[str]:
    for n in names:
        m = re.search(r'"%s"\s*:\s*"([^"]+)"' % n, html)
        if m:
            return m.group(1)
    return None


def _meta(html: str, kind: str) -> Optional[str]:
    m = re.search(r'<meta[^>]+property="article:%s_time"[^>]+content="([^"]+)"' % kind, html)
    return m.group(1) if m else None


def article_dates(html: str) -> Dict[str, Optional[str]]:
    return {
        "published": _json_field(html, "datePublished", "firstPublished") or _meta(html, "published"),
        "modified": _json_field(html, "dateModified", "lastPublished", "lastUpdated") or _meta(html, "modified"),
    }
