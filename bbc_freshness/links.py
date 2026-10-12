"""Link normalisation and extraction (HTML anchors and markdown)."""
import re
from html.parser import HTMLParser
from typing import Dict, Optional
from urllib.parse import urljoin, urlparse

BBC_HOSTS = {"www.bbc.co.uk", "www.bbc.com", "bbc.co.uk", "bbc.com"}
# Sport content: articles, live pages, videos.
CONTENT_PATH = re.compile(r"^/sport/(?:[\w-]+/)*(?:articles|live|videos?)/[\w-]+$")
MD_LINK = re.compile(r"\[([^\]]*)\]\((\S+?)(?:\s+\"[^\"]*\")?\)")
BARE_URL = re.compile(r"https?://[^\s)\]>\"']+")


def normalize(href: str, base: str) -> Optional[str]:
    """Canonical URL for a BBC Sport content link, or None if not one."""
    u = urlparse(urljoin(base, href.strip()))
    if u.netloc not in BBC_HOSTS:
        return None
    path = u.path.rstrip("/")
    return "https://www.bbc.co.uk" + path if CONTENT_PATH.match(path) else None


def _add(out: Dict[str, str], key: Optional[str], text: str) -> None:
    if key and (key not in out or len(text) > len(out[key])):
        out[key] = text


class _Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href, self._text = dict(attrs).get("href"), []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.found.append((self._href, " ".join("".join(self._text).split())))
            self._href = None


def links_from_html(html: str, base: str) -> Dict[str, str]:
    """{url: headline} from a live HTML page."""
    p = _Anchors()
    p.feed(html)
    out: Dict[str, str] = {}
    for href, text in p.found:
        _add(out, normalize(href, base), text)
    return out


def links_from_markdown(md: str, base: str) -> Dict[str, str]:
    """{url: headline} from Tavily's markdown content."""
    out: Dict[str, str] = {}
    for text, href in MD_LINK.findall(md or ""):
        _add(out, normalize(href, base), " ".join(text.split()))
    for href in BARE_URL.findall(md or ""):
        key = normalize(href, base)
        if key:
            out.setdefault(key, "")
    return out
