# BBC Sport – Tavily Extract Freshness POC

Evaluates whether the Tavily **Extract** API returns the latest BBC Sport homepage
content, compared with the live site. (Search API is not used.)

## Method
1. Fetch the live homepage; record links, headlines, HTTP status, timestamp.
2. Extract the same page via Tavily Extract in `basic` and `advanced` modes.
3. Compare link sets (common / live-only / Tavily-only); read publish/modified
   dates of differing articles from the live article pages.
4. Extract live-only articles directly via Tavily to separate a homepage
   *coverage/freshness* difference from an article *extraction failure*.
5. Produce a conservative verdict: `NO_DIFFERENCE`, `HOMEPAGE_COVERAGE_DIFFERENCE`,
   `POSSIBLE_FRESHNESS_LAG` or `INCONCLUSIVE`.

## Layout
```
bbc_freshness/
  config.py         settings, .env loading
  http_client.py    HTTP helper
  links.py          URL normalisation, link extraction
  dates.py          publish/modified date extraction
  tavily_client.py  Tavily Extract client
  compare.py        set comparison
  verdict.py        evidence -> verdict
  report.py         report.json / report.md
  runner.py         orchestration
tests/test_poc.py   unit tests (offline)
```

## Run
Python 3.9+, no dependencies.
```
cp .env.example .env        # add your TAVILY_API_KEY
python3 -m bbc_freshness    # optional: --url, --max-direct N
python3 -m unittest discover -s tests
```
Output goes to `results/run_<UTC timestamp>/`: `report.md`, `report.json`,
`live.html`, and the raw Tavily responses.

## Limitations
- Live fetch is plain HTTP (no JS rendering); BBC may personalise by region.
- Date extraction is regex best-effort.
- One run is a snapshot; repeat at different times before concluding.
