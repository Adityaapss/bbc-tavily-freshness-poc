"""Settings and .env loading."""
import os
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAVILY_EXTRACT_URL = "https://api.tavily.com/extract"
DEFAULT_PAGE = "https://www.bbc.co.uk/sport"
BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


@dataclass(frozen=True)
class Settings:
    api_key: str
    page_url: str = DEFAULT_PAGE
    max_direct: int = 5
    max_date_lookups: int = 40
    results_dir: Path = ROOT / "results"


def load_dotenv(path: Path = ROOT / ".env") -> None:
    """Minimal .env reader; real environment variables take precedence."""
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_api_key() -> str:
    load_dotenv()
    key = os.environ.get("TAVILY_API_KEY", "")
    if not key:
        raise SystemExit("TAVILY_API_KEY is not set (use environment or a .env file).")
    return key
