"""Conservative interpretation of the evidence."""
from typing import Dict, List, Optional

NO_DIFFERENCE = "NO_DIFFERENCE"
COVERAGE = "HOMEPAGE_COVERAGE_DIFFERENCE"
FRESHNESS = "POSSIBLE_FRESHNESS_LAG"
INCONCLUSIVE = "INCONCLUSIVE"


def _stamp(dates: Dict[str, dict], url: str) -> Optional[str]:
    d = dates.get(url) or {}
    return d.get("modified") or d.get("published")


def decide(live_ok: bool, tavily_ok: bool, cmp_adv: dict,
           direct: List[dict], dates: Dict[str, dict]) -> Dict[str, str]:
    if not live_ok:
        return _v(INCONCLUSIVE, "Live page could not be fetched or parsed.")
    if not tavily_ok:
        return _v(INCONCLUSIVE, "Tavily returned no usable links.")

    parts = [f"Advanced overlap with live: {cmp_adv['overlap_pct_of_live']}% "
             f"({len(cmp_adv['common'])} common, {len(cmp_adv['live_only'])} live-only, "
             f"{len(cmp_adv['tavily_only'])} tavily-only)."]
    ok = [d for d in direct if d["extracted"]]
    if direct:
        parts.append(f"Direct extraction succeeded for {len(ok)}/{len(direct)} live-only articles.")

    if not cmp_adv["live_only"]:
        label = NO_DIFFERENCE
        parts.append("No live-only links: no evidence of staleness in this run.")
    elif direct and len(ok) == len(direct):
        live_ts = [t for t in (_stamp(dates, u) for u in cmp_adv["live_only"]) if t]
        tav_ts = [t for t in (_stamp(dates, u) for u in cmp_adv["tavily_only"]) if t]
        if live_ts and tav_ts and max(tav_ts) < min(live_ts):
            label = FRESHNESS
            parts.append("Every Tavily-only article is older than every live-only article, and the "
                         "missing articles extract fine directly: consistent with an older homepage "
                         "snapshot. Repeat over time before concluding.")
        else:
            label = COVERAGE
            parts.append("Missing articles extract fine and timestamps do not show a clean age split: "
                         "points to a homepage coverage difference, not an extraction failure.")
    else:
        label = INCONCLUSIVE
        parts.append("Some live-only articles could not be extracted directly, or no direct test ran.")
    parts.append("A single run is a snapshot; BBC changes constantly.")
    return _v(label, " ".join(parts))


def _v(label: str, text: str) -> Dict[str, str]:
    return {"label": label, "summary": f"{label}: {text}"}
