"""Fetch NBA player IDs from Basketball-Reference league totals pages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from .utils import fetch_html, make_session, parse_player_id_from_url

BASE_URL = "https://www.basketball-reference.com"


@dataclass
class NbaSeasonConfig:
    start_season: int = 2011
    end_season: int = 2025

    def seasons(self) -> list[int]:
        return list(range(self.start_season, self.end_season + 1))


def league_totals_url(season: int) -> str:
    return f"{BASE_URL}/leagues/NBA_{season}_totals.html"


def _extract_rows_from_season_html(season: int, html: str) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="totals_stats")
    if table is None:
        return []

    body = table.find("tbody")
    if body is None:
        return []

    rows: list[dict] = []
    for tr in body.find_all("tr"):
        if "class" in tr.attrs and "thead" in tr.attrs["class"]:
            continue
        player_cell = tr.find(["th", "td"], {"data-stat": "name_display"})
        if player_cell is None:
            continue
        link = player_cell.find("a")
        if link is None or not link.get("href"):
            continue
        player_name = link.get_text(strip=True)
        rel_url = link["href"]
        player_url = urljoin(BASE_URL, rel_url)
        player_id = parse_player_id_from_url(player_url)
        if not player_id:
            continue
        rows.append(
            {
                "season": season,
                "player_name": player_name,
                "nba_player_id": player_id,
                "nba_player_url": player_url,
            }
        )
    return rows


def fetch_nba_player_ids_for_seasons(seasons: Iterable[int]) -> pd.DataFrame:
    """Fetch player IDs by season from league totals pages."""
    session = make_session()
    all_rows: list[dict] = []

    for season in seasons:
        url = league_totals_url(season)
        html = fetch_html(session, url)
        rows = _extract_rows_from_season_html(season, html)
        all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    if df.empty:
        return df
    df = df.sort_values(["season", "nba_player_id"]).reset_index(drop=True)
    return df


def get_unique_nba_players(season_df: pd.DataFrame) -> pd.DataFrame:
    """Return one row per unique nba player id with first seen season."""
    if season_df.empty:
        return season_df.copy()
    unique_df = (
        season_df.sort_values("season")
        .drop_duplicates(subset=["nba_player_id"], keep="first")
        .reset_index(drop=True)
    )
    return unique_df
