"""
Google Sheets client for the member roster.

Reads a single worksheet via the public Google Sheets REST API. The sheet is
expected to follow the column layout used by the WUCG roster form (the same
layout the legacy Django `member/googlesheet_scraper.py` targeted).

Required environment:
    GOOGLE_SHEET_ID   spreadsheet id
    GOOGLE_API_KEY    API key with Sheets read permission

Schema for each roster row (0-indexed), with tolerant handling for short rows:
    0  register_date          e.g. "03/12/2025 14:22:01"
    1  leetcode_username
    2  server_region          any value containing "cn" => CN, else US
    3  problems_per_week      integer or blank
    4  start_date             "YYYY-MM-DD"
    5  expire_date            "YYYY-MM-DD" or blank
    6  scheduled_problems     whitespace-separated problem codes, or blank
    7  email                  identity key
    8  mode                   e.g. "Normal", "Free"
    9  display_name           optional, falls back to leetcode_username
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass
from typing import Any

import requests

logger = logging.getLogger(__name__)

DEFAULT_RANGE = "A1:Z"


@dataclass
class Member:
    email: str
    leetcode_username: str
    display_name: str
    server_region: str  # "US" or "CN"
    register_date: str
    start_date: str
    expire_date: str
    mode: str
    problems_per_week: int | None
    scheduled_problems: list[str]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class GoogleSheetClient:
    def __init__(self, spreadsheet_id: str, api_key: str, sheet_range: str = DEFAULT_RANGE) -> None:
        if not spreadsheet_id or not api_key:
            raise ValueError("spreadsheet_id and api_key are required")
        self.spreadsheet_id = spreadsheet_id
        self.api_key = api_key
        self.sheet_range = sheet_range

    @classmethod
    def from_env(cls) -> "GoogleSheetClient":
        return cls(
            spreadsheet_id=os.environ["GOOGLE_SHEET_ID"],
            api_key=os.environ["GOOGLE_API_KEY"],
            sheet_range=os.environ.get("GOOGLE_SHEET_RANGE", DEFAULT_RANGE),
        )

    def fetch_raw(self) -> list[list[str]]:
        url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/{self.spreadsheet_id}"
            f"/values/{self.sheet_range}?alt=json&key={self.api_key}"
        )
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("values", [])

    def fetch_members(self) -> list[Member]:
        rows = self.fetch_raw()
        if not rows:
            logger.warning("Sheet %s returned no rows", self.spreadsheet_id)
            return []

        members: list[Member] = []
        for row_idx, row in enumerate(rows[1:], start=2):
            if len(row) < 8 or not row[1].strip():
                # leetcode_username or email missing — skip
                logger.info("Skipping sheet row %d (incomplete)", row_idx)
                continue

            def _cell(idx: int, default: str = "") -> str:
                return row[idx].strip() if idx < len(row) and row[idx] else default

            raw_region = _cell(2).lower()
            server_region = "CN" if "cn" in raw_region else "US"

            try:
                problems_per_week: int | None = int(_cell(3)) if _cell(3) else None
            except ValueError:
                problems_per_week = None

            scheduled_problems = [tok for tok in _cell(6).split() if tok]
            display_name = _cell(9) or _cell(1)

            members.append(
                Member(
                    email=_cell(7),
                    leetcode_username=_cell(1),
                    display_name=display_name,
                    server_region=server_region,
                    register_date=_cell(0),
                    start_date=_cell(4),
                    expire_date=_cell(5),
                    mode=_cell(8),
                    problems_per_week=problems_per_week,
                    scheduled_problems=scheduled_problems,
                )
            )
        return members


if __name__ == "__main__":
    import json

    logging.basicConfig(level=logging.INFO)
    client = GoogleSheetClient.from_env()
    print(json.dumps([m.as_dict() for m in client.fetch_members()], indent=2))
