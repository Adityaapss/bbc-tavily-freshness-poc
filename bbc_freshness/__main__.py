import argparse

from .config import DEFAULT_PAGE, Settings, get_api_key
from .runner import run


def main() -> None:
    ap = argparse.ArgumentParser(prog="bbc_freshness", description=__doc__)
    ap.add_argument("--url", default=DEFAULT_PAGE, help="page to test")
    ap.add_argument("--max-direct", type=int, default=5, help="live-only articles to extract directly")
    a = ap.parse_args()
    run(Settings(api_key=get_api_key(), page_url=a.url, max_direct=a.max_direct))


if __name__ == "__main__":
    main()
