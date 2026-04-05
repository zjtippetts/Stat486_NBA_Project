"""Fetch NBA player profile fields and required tables from player pages."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import re
from typing import Iterable
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from .utils import (
    extract_table_by_id,
    fetch_html,
    make_session,
    parse_cbb_id_from_url,
    parse_recruiting_rank,
    safe_to_numeric,
)

BASE_URL = "https://www.basketball-reference.com"
NBA_TABLE_ID_CANDIDATES = {
    "totals": ["totals_stats", "totals"],
    "per100": ["per_poss"],
    "advanced": ["advanced"],
    "adj_shooting": ["adj_shooting"],
    "play_by_play": ["pbp"],
    "shooting": ["shooting"],
}


def _extract_bio_fields(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    info = soup.find("div", id="info")

    birthday = None
    recruiting_year = None
    recruiting_rank = None
    college_url = None

    birth_span = soup.find("span", {"itemprop": "birthDate"})
    if birth_span is not None:
        birthday = (
            birth_span.get("data-birth")
            or birth_span.get("datetime")
            or birth_span.get_text(strip=True)
        )
    if birthday is None:
        fallback_birth = soup.find("span", id=re.compile(r"^necro-birth$"))
        if fallback_birth is not None:
            birthday = fallback_birth.get("data-birth") or fallback_birth.get_text(strip=True)

    text_blob = info.get_text(" ", strip=True) if info else soup.get_text(" ", strip=True)
    recruiting_year, recruiting_rank = parse_recruiting_rank(text_blob)

    if info is not None:
        college_link = info.find("a", href=re.compile(r"/cbb/players/.*\.html"))
        if college_link is not None and college_link.get("href"):
            college_url = urljoin(BASE_URL, college_link["href"])

    if college_url is None:
        fallback = soup.find("a", href=re.compile(r"/cbb/players/.*\.html"))
        if fallback is not None and fallback.get("href"):
            college_url = urljoin(BASE_URL, fallback["href"])

    # Optional raw fields for future modeling; Deliverable 3 v1 uses Pos/age from tables + birthday instead.
    height_inches = None
    weight_lb = None
    if info is not None:
        blob = info.get_text(" ", strip=True)
        # e.g. "6-10 , 253lb" in #info (avoid matching season labels like 2011-12: feet are 4–7).
        hm = re.search(r"\b([4-7])-(\d{1,2})\b", blob)
        if hm:
            ft, inch = int(hm.group(1)), int(hm.group(2))
            if inch <= 11:
                height_inches = float(ft * 12 + inch)
        wm = re.search(r"\b(\d{2,3})\s*lb", blob, re.I)
        if wm:
            weight_lb = float(wm.group(1))

    return {
        "birthday": birthday,
        "recruiting_year": recruiting_year,
        "recruiting_rank": recruiting_rank,
        "college_url": college_url,
        "college_player_id": parse_cbb_id_from_url(college_url),
        "height_inches": height_inches,
        "weight_lb": weight_lb,
    }


def fetch_nba_player_profiles(
    player_rows: Iterable[dict],
    *,
    max_workers: int = 5,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch player profile fields and required tables.

    Returns:
        (profile_fields_df, nba_tables_long_df)
    """
    def _scrape_player(player: dict) -> tuple[dict, list[pd.DataFrame]]:
        session = make_session()
        nba_player_id = player["nba_player_id"]
        nba_player_url = player["nba_player_url"]

        profile_base = {
            "nba_player_id": nba_player_id,
            "nba_player_url": nba_player_url,
            "scrape_status": "ok",
            "error": None,
        }

        local_tables: list[pd.DataFrame] = []
        try:
            html = fetch_html(session, nba_player_url)
            bio_fields = _extract_bio_fields(html)
            profile_row = {**profile_base, **bio_fields}

            for output_table_id, candidates in NBA_TABLE_ID_CANDIDATES.items():
                table_df = None
                for table_id in candidates:
                    table_df = extract_table_by_id(html, table_id)
                    if table_df is not None and not table_df.empty:
                        break
                if table_df is None or table_df.empty:
                    continue
                table_df = safe_to_numeric(table_df)
                table_df.insert(0, "table_id", output_table_id)
                table_df.insert(0, "nba_player_id", nba_player_id)
                local_tables.append(table_df)
        except Exception as exc:  # noqa: BLE001
            profile_row = {
                **profile_base,
                "birthday": None,
                "recruiting_year": None,
                "recruiting_rank": None,
                "college_url": None,
                "college_player_id": None,
                "height_inches": None,
                "weight_lb": None,
                "scrape_status": "error",
                "error": str(exc),
            }
        return profile_row, local_tables

    players = list(player_rows)
    profile_rows: list[dict] = []
    table_rows: list[pd.DataFrame] = []

    max_workers = min(max_workers, max(1, len(players)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for profile_row, local_tables in executor.map(_scrape_player, players):
            profile_rows.append(profile_row)
            table_rows.extend(local_tables)

    profile_df = pd.DataFrame(profile_rows)
    tables_long_df = pd.concat(table_rows, ignore_index=True) if table_rows else pd.DataFrame()
    return profile_df, tables_long_df
