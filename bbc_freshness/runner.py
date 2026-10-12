"""Orchestrates the POC steps."""
import json
from datetime import datetime, timezone
from pathlib import Path

from . import report as report_mod
from .compare import compare, compare_modes
from .config import BROWSER_UA, Settings
from .dates import article_dates
from .http_client import request, utc_now
from .links import links_from_html, links_from_markdown
from .tavily_client import TavilyExtract, first_content
from .verdict import decide

MODES = ("basic", "advanced")
LIVE_HEADERS = {"User-Agent": BROWSER_UA, "Accept-Language": "en-GB,en;q=0.9"}


def _new_run_dir(settings: Settings) -> Path:
    d = settings.results_dir / ("run_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    d.mkdir(parents=True)
    return d


def fetch_live(settings: Settings, out: Path) -> dict:
    ts = utc_now()
    r = request(settings.page_url, headers=LIVE_HEADERS)
    (out / "live.html").write_text(r.text)
    links = links_from_html(r.text, settings.page_url) if r.status == 200 else {}
    return {"retrieved_at": ts, "http_status": r.status, "elapsed_s": round(r.elapsed_s, 2),
            "article_count": len(links), "links": links}


def extract_homepage(settings: Settings, tavily: TavilyExtract, out: Path) -> dict:
    res = {}
    for mode in MODES:
        resp = tavily.extract([settings.page_url], mode)
        content = first_content(resp)
        (out / f"tavily_{mode}.json").write_text(json.dumps(resp, indent=2))
        (out / f"tavily_{mode}.md").write_text(content)
        links = links_from_markdown(content, settings.page_url)
        res[mode] = {"retrieved_at": resp["retrieved_at"], "http_status": resp["http_status"],
                     "elapsed_s": resp["elapsed_s"], "content_chars": len(content),
                     "article_count": len(links), "links": links,
                     "failed_results": (resp["data"] or {}).get("failed_results")}
    return res


def lookup_dates(urls, limit: int) -> dict:
    out = {}
    for u in sorted(urls)[:limit]:
        r = request(u, headers={"User-Agent": BROWSER_UA})
        out[u] = {"http_status": r.status, **(article_dates(r.text) if r.status == 200 else {})}
    return out


def direct_extract(tavily: TavilyExtract, urls, dates: dict) -> list:
    rows = []
    for u in urls:
        resp = tavily.extract([u], "advanced")
        results = (resp["data"] or {}).get("results") or []
        content = results[0].get("raw_content", "") if results else ""
        rows.append({"url": u, "retrieved_at": resp["retrieved_at"], "http_status": resp["http_status"],
                     "extracted": bool(content), "content_chars": len(content),
                     "failed": (resp["data"] or {}).get("failed_results"), "dates": dates.get(u)})
    return rows


def run(settings: Settings) -> Path:
    out = _new_run_dir(settings)
    tavily = TavilyExtract(settings.api_key)
    rep = {"page": settings.page_url, "started_at": utc_now()}

    print("[1/5] Fetching live page...")
    rep["live"] = fetch_live(settings, out)
    print(f"      HTTP {rep['live']['http_status']}, {rep['live']['article_count']} links")

    print("[2/5] Tavily extract (basic + advanced)...")
    home = extract_homepage(settings, tavily, out)
    for m in MODES:
        rep[f"tavily_{m}"] = home[m]
        print(f"      {m}: HTTP {home[m]['http_status']}, {home[m]['article_count']} links")

    print("[3/5] Comparing...")
    live = rep["live"]["links"]
    cmp = {m: compare(live, home[m]["links"]) for m in MODES}
    cmp["basic_vs_advanced"] = compare_modes(home["basic"]["links"], home["advanced"]["links"])
    rep["comparison"] = cmp

    print("[4/5] Reading article dates...")
    differing = set(cmp["basic"]["live_only"]) | set(cmp["basic"]["tavily_only"]) \
        | set(cmp["advanced"]["live_only"]) | set(cmp["advanced"]["tavily_only"])
    rep["article_dates"] = lookup_dates(differing, settings.max_date_lookups)

    print("[5/5] Direct extraction of live-only articles...")
    targets = sorted(cmp["advanced"]["live_only"])[:settings.max_direct]
    rep["direct_extraction"] = direct_extract(tavily, targets, rep["article_dates"])

    rep["verdict"] = decide(
        live_ok=rep["live"]["http_status"] == 200 and bool(live),
        tavily_ok=home["advanced"]["http_status"] == 200 and bool(home["advanced"]["links"]),
        cmp_adv=cmp["advanced"], direct=rep["direct_extraction"], dates=rep["article_dates"])
    rep["finished_at"] = utc_now()
    report_mod.write(out, rep)
    print("\n" + rep["verdict"]["summary"] + f"\n\nResults: {out}")
    return out
