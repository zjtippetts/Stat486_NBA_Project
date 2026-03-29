"""Fetch college tables from Sports-Reference college player pages."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable

import pandas as pd

logger = logging.getLogger(__name__)

from .utils import extract_table_by_id, fetch_html, make_session, safe_to_numeric

CBB_TABLE_ID_CANDIDATES = {
    "totals": ["players_totals", "totals"],
    "per100": ["players_per_poss", "per_poss"],
    "advanced": ["players_advanced", "advanced"],
}


def fetch_college_profiles(
    college_rows: Iterable[dict],
    *,
    max_workers: int = 5,
    progress_every: int = 0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetch required college tables for a set of college URLs.

    Returns:
        (college_tables_long_df, college_failures_df)
    """
    def _scrape_college(row: dict) -> tuple[list[pd.DataFrame], dict | None]:
        session = make_session()
        college_player_id = row["college_player_id"]
        college_url = row["college_url"]

        if not college_url:
            return [], {"college_player_id": college_player_id, "college_url": college_url, "error": "missing_url"}

        try:
            html = fetch_html(session, college_url)
        except Exception as exc:  # noqa: BLE001
            return [], {"college_player_id": college_player_id, "college_url": college_url, "error": str(exc)}

        local_rows: list[pd.DataFrame] = []
        for output_table_id, candidates in CBB_TABLE_ID_CANDIDATES.items():
            table_df = None
            for table_id in candidates:
                table_df = extract_table_by_id(html, table_id)
                if table_df is not None and not table_df.empty:
                    break
            if table_df is None or table_df.empty:
                continue
            table_df = safe_to_numeric(table_df)
            table_df.insert(0, "table_id", output_table_id)
            table_df.insert(0, "college_url", college_url)
            table_df.insert(0, "college_player_id", college_player_id)
            local_rows.append(table_df)
        return local_rows, None

    rows = list(college_rows)
    all_table_rows: list[pd.DataFrame] = []
    failures: list[dict] = []
    max_workers = min(max_workers, max(1, len(rows)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        if progress_every > 0 and len(rows) > 1:
            futures = {executor.submit(_scrape_college, row): row for row in rows}
            total = len(futures)
            done = 0
            for fut in as_completed(futures):
                done += 1
                local_rows, failure = fut.result()
                all_table_rows.extend(local_rows)
                if failure is not None:
                    failures.append(failure)
                if done % progress_every == 0 or done == total:
                    logger.info("College pages: %s / %s complete", done, total)
        else:
            for local_rows, failure in executor.map(_scrape_college, rows):
                all_table_rows.extend(local_rows)
                if failure is not None:
                    failures.append(failure)

    failures_df = pd.DataFrame(failures)
    if not all_table_rows:
        return pd.DataFrame(), failures_df

    return pd.concat(all_table_rows, ignore_index=True), failures_df
