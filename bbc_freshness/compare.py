"""Set comparison of link collections."""
from typing import Dict, Iterable


def compare(live: Iterable[str], other: Iterable[str]) -> Dict[str, object]:
    L, T = set(live), set(other)
    return {
        "common": sorted(L & T),
        "live_only": sorted(L - T),
        "tavily_only": sorted(T - L),
        "overlap_pct_of_live": round(100 * len(L & T) / len(L), 1) if L else None,
    }


def compare_modes(basic: Iterable[str], advanced: Iterable[str]) -> Dict[str, object]:
    b, a = set(basic), set(advanced)
    return {"common": len(a & b), "basic_only": sorted(b - a), "advanced_only": sorted(a - b),
            "identical": a == b}
