"""Shared utilities for Basketball-Reference and Sports-Reference scraping."""

from __future__ import annotations

import io
import random
import re
import time
from typing import Optional

import pandas as pd
import requests
from bs4 import BeautifulSoup, Comment
from curl_cffi import requests as curl_requests
from curl_cffi.requests.exceptions import HTTPError as CurlHTTPError
from requests.exceptions import HTTPError as RequestsHTTPError

BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}


def make_session() -> requests.Session:
    """Create a requests session with default headers."""
    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    return session


def fetch_html(
    session: requests.Session,
    url: str,
    *,
    max_retries: int = 6,
    timeout: int = 25,
    min_delay: float = 0.25,
    max_delay: float = 0.9,
) -> str:
    """Fetch HTML with retry/backoff; extra wait on HTTP 429 (rate limit)."""
    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            if "basketball-reference.com" in url or "sports-reference.com" in url:
                response = curl_requests.get(url, impersonate="chrome", timeout=timeout)
            else:
                response = session.get(url, timeout=timeout)
            response.raise_for_status()
            time.sleep(random.uniform(min_delay, max_delay))
            return response.text
        except (RequestsHTTPError, CurlHTTPError) as exc:
            last_error = exc
            if exc.response is not None and exc.response.status_code == 429:
                ra = exc.response.headers.get("Retry-After")
                if ra and str(ra).isdigit():
                    sleep_s = float(ra) + random.uniform(0, 3)
                else:
                    sleep_s = 25.0 + attempt * 20 + random.uniform(0, 8)
                time.sleep(sleep_s)
                continue
            sleep_s = (attempt + 1) * 1.5
            time.sleep(sleep_s)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            sleep_s = (attempt + 1) * 1.5
            time.sleep(sleep_s)
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"Failed to fetch URL: {url}")


def flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Flatten potential MultiIndex columns after read_html."""
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [
            "_".join(str(part) for part in col if str(part) != "nan").strip("_")
            for col in df.columns
        ]
    else:
        df.columns = [str(c) for c in df.columns]
    return df


def normalize_table(df: pd.DataFrame) -> pd.DataFrame:
    """Clean common table artifacts and standardize column naming."""
    df = flatten_columns(df).copy()
    df = df.loc[:, ~df.columns.str.startswith("Unnamed")]
    if "Rk" in df.columns:
        df = df[df["Rk"] != "Rk"]
    if "Player" in df.columns:
        df = df[df["Player"] != "Player"]
    df.columns = [
        c.strip().replace("%", "pct").replace("/", "_").replace(" ", "_")
        for c in df.columns
    ]
    return df.reset_index(drop=True)


def _read_first_html_table(html_fragment: str) -> Optional[pd.DataFrame]:
    """Read first table from HTML fragment and return normalized DataFrame."""
    try:
        tables = pd.read_html(io.StringIO(html_fragment))
        if not tables:
            return None
        return normalize_table(tables[0])
    except ValueError:
        return None


def extract_table_by_id(html: str, table_id: str) -> Optional[pd.DataFrame]:
    """
    Extract a table by id.

    Basketball-Reference/Sports-Reference often hide tables in HTML comments.
    This checks visible HTML first, then comment blocks.
    """
    soup = BeautifulSoup(html, "lxml")

    table = soup.find("table", id=table_id)
    if table is not None:
        parsed = _read_first_html_table(str(table))
        if parsed is not None:
            return parsed

    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if f'id="{table_id}"' in comment:
            parsed = _read_first_html_table(comment)
            if parsed is not None:
                return parsed

    return None


def parse_player_id_from_url(player_url: str) -> Optional[str]:
    """Parse nba player id from /players/x/xxxxxxx.html URL."""
    match = re.search(r"/players/[a-z]/([a-z0-9]+)\.html", player_url)
    return match.group(1) if match else None


def parse_cbb_id_from_url(college_url: Optional[str]) -> Optional[str]:
    """Parse college player id from /cbb/players/slug.html URL."""
    if not college_url:
        return None
    match = re.search(r"/cbb/players/([^/]+)\.html", college_url)
    return match.group(1) if match else None


def parse_recruiting_rank(text: str) -> tuple[Optional[int], Optional[int]]:
    """
    Parse recruiting year and rank from free-text.

    Example expected text:
    "Recruiting Rank: 2017 (30)"
    """
    year_match = re.search(r"Recruiting Rank:\s*(\d{4})", text)
    rank_match = re.search(r"Recruiting Rank:.*?\((\d+)\)", text)
    recruiting_year = int(year_match.group(1)) if year_match else None
    recruiting_rank = int(rank_match.group(1)) if rank_match else None
    return recruiting_year, recruiting_rank


def safe_to_numeric(df: pd.DataFrame) -> pd.DataFrame:
    """Convert numeric-looking columns to numeric where possible."""
    out = df.copy()
    for col in out.columns:
        if col in {"Player", "Season", "Tm", "Team", "Pos", "Lg", "Awards"}:
            continue
        converted = pd.to_numeric(out[col], errors="coerce")
        # Keep original column if conversion produced all nulls.
        if converted.notna().any():
            out[col] = converted
    return out
