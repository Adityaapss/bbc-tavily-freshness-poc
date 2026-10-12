import unittest

from bbc_freshness.compare import compare, compare_modes
from bbc_freshness.dates import article_dates
from bbc_freshness.links import links_from_html, links_from_markdown, normalize
from bbc_freshness.verdict import COVERAGE, FRESHNESS, INCONCLUSIVE, NO_DIFFERENCE, decide

BASE = "https://www.bbc.co.uk/sport"
A = "https://www.bbc.co.uk/sport/football/articles/aaa"
B = "https://www.bbc.co.uk/sport/cricket/articles/bbb"


class LinkTests(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(normalize("/sport/football/articles/aaa?x=1#y", BASE), A)
        self.assertEqual(normalize(A + "/", BASE), A)
        self.assertIsNone(normalize("/news/articles/zzz", BASE))
        self.assertIsNone(normalize("https://example.com/sport/football/articles/aaa", BASE))

    def test_html_and_markdown(self):
        html = '<a href="/sport/football/articles/aaa"><span>Big  win</span></a><a href="/x">no</a>'
        self.assertEqual(links_from_html(html, BASE), {A: "Big win"})
        md = f"[Story]({A}) and [Other]({B} \"t\") and [x](https://example.com)"
        self.assertEqual(links_from_markdown(md, BASE), {A: "Story", B: "Other"})


class CompareTests(unittest.TestCase):
    def test_compare(self):
        c = compare([A, B], [A])
        self.assertEqual((c["common"], c["live_only"], c["tavily_only"]), ([A], [B], []))
        self.assertEqual(c["overlap_pct_of_live"], 50.0)
        self.assertTrue(compare_modes([A], [A])["identical"])


class DateTests(unittest.TestCase):
    def test_json(self):
        d = article_dates('{"datePublished":"2026-01-01T00:00:00Z","dateModified":"2026-01-02T00:00:00Z"}')
        self.assertEqual(d["published"], "2026-01-01T00:00:00Z")
        self.assertEqual(d["modified"], "2026-01-02T00:00:00Z")


class VerdictTests(unittest.TestCase):
    ok = [{"extracted": True}]

    def test_freshness(self):
        c = compare([B], [A])
        dates = {A: {"modified": "2026-01-01"}, B: {"modified": "2026-01-02"}}
        self.assertEqual(decide(True, True, c, self.ok, dates)["label"], FRESHNESS)

    def test_coverage_when_no_age_split(self):
        c = compare([B], [A])
        dates = {A: {"modified": "2026-01-03"}, B: {"modified": "2026-01-02"}}
        self.assertEqual(decide(True, True, c, self.ok, dates)["label"], COVERAGE)

    def test_no_difference_and_inconclusive(self):
        self.assertEqual(decide(True, True, compare([A], [A]), [], {})["label"], NO_DIFFERENCE)
        self.assertEqual(decide(False, True, compare([A], [A]), [], {})["label"], INCONCLUSIVE)
        self.assertEqual(decide(True, True, compare([B], [A]), [{"extracted": False}], {})["label"], INCONCLUSIVE)


if __name__ == "__main__":
    unittest.main()
