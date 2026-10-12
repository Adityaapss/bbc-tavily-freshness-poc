"""Writes report.json / report.md."""
import json
from pathlib import Path


def write(out_dir: Path, report: dict) -> None:
    (out_dir / "report.json").write_text(json.dumps(report, indent=2))
    (out_dir / "report.md").write_text(render_markdown(report))


def render_markdown(r: dict) -> str:
    L = [f"# BBC Sport freshness POC\n\nPage: {r['page']}  \nRun: {r['started_at']} -> {r['finished_at']}\n",
         "## Retrieval\n",
         "| Source | HTTP | Retrieved at (UTC) | Elapsed s | Links |", "|---|---|---|---|---|",
         f"| Live | {r['live']['http_status']} | {r['live']['retrieved_at']} | "
         f"{r['live']['elapsed_s']} | {r['live']['article_count']} |"]
    for d in ("basic", "advanced"):
        t = r[f"tavily_{d}"]
        L.append(f"| Tavily {d} | {t['http_status']} | {t['retrieved_at']} | {t['elapsed_s']} | {t['article_count']} |")
    L.append("\n## Comparison vs live\n")
    for d in ("basic", "advanced"):
        c = r["comparison"][d]
        L.append(f"**{d}**: overlap {c['overlap_pct_of_live']}% of live; common {len(c['common'])}, "
                 f"live-only {len(c['live_only'])}, tavily-only {len(c['tavily_only'])}\n")
        for label, key in (("Live-only (missing from Tavily)", "live_only"),
                           ("Tavily-only (not on live now)", "tavily_only")):
            if c[key]:
                L.append(f"- {label}:")
                for u in c[key]:
                    dt = r["article_dates"].get(u) or {}
                    L.append(f"  - {u} — published {dt.get('published')}, modified {dt.get('modified')}")
        L.append("")
    b = r["comparison"]["basic_vs_advanced"]
    L.append(f"**Basic vs advanced**: identical={b['identical']}; {b['common']} common; "
             f"basic-only {len(b['basic_only'])}, advanced-only {len(b['advanced_only'])}\n")
    L += ["## Direct article extraction (advanced)\n",
          "| URL | HTTP | Extracted | Chars | Published | Modified |", "|---|---|---|---|---|---|"]
    for d in r["direct_extraction"]:
        dt = d.get("dates") or {}
        L.append(f"| {d['url']} | {d['http_status']} | {d['extracted']} | {d['content_chars']} | "
                 f"{dt.get('published')} | {dt.get('modified')} |")
    L += [f"\n## Verdict\n\n{r['verdict']['summary']}\n",
          "## Limitations\n",
          "- Live fetch is plain HTTP (no JavaScript rendering).",
          "- BBC may personalise by region; live and Tavily fetches come from different IPs seconds apart.",
          "- Date extraction is regex best-effort.",
          "- One run is a snapshot; repeat over time for confidence.\n"]
    return "\n".join(L)
