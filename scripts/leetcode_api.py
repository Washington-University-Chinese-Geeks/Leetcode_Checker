"""
LeetCode GraphQL client.

Standalone (no Django) version of the scraper originally in
`check/leetcode_scraper.py`. Used by the GitHub Actions collector to pull
recent AC submissions and public profile data for each tracked user.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from warnings import filterwarnings

import requests

filterwarnings("ignore")

logger = logging.getLogger(__name__)


RECENT_AC_QUERY = """
query recentAcSubmissions($username: String!, $limit: Int!) {
  recentAcSubmissionList(username: $username, limit: $limit) {
    id
    title
    titleSlug
    timestamp
  }
}
"""

USER_PROFILE_QUERY = """
query userPublicProfile($username: String!) {
  matchedUser(username: $username) {
    username
    profile {
      ranking
      userAvatar
      realName
      countryName
      solutionCount
      reputation
    }
  }
}
"""

USER_PROBLEMS_SOLVED_QUERY = """
query userProblemsSolved($username: String!) {
  allQuestionsCount { difficulty count }
  matchedUser(username: $username) {
    problemsSolvedBeatsStats { difficulty percentage }
    submitStatsGlobal {
      acSubmissionNum { difficulty count }
    }
  }
}
"""

USER_CALENDAR_QUERY = """
query userProfileCalendar($username: String!, $year: Int) {
  matchedUser(username: $username) {
    userCalendar(year: $year) {
      activeYears
      streak
      totalActiveDays
      submissionCalendar
    }
  }
}
"""


class LeetCodeClient:
    """Thin wrapper around the public LeetCode GraphQL endpoint."""

    US_ENDPOINT = "https://leetcode.com/graphql"
    CN_ENDPOINT = "https://leetcode.cn/graphql"

    def __init__(self, server_region: str = "US", timeout: int = 15) -> None:
        if server_region not in ("US", "CN"):
            raise ValueError(f"Invalid server region: {server_region!r}")
        self.server_region = server_region
        self.base_url = self.US_ENDPOINT if server_region == "US" else self.CN_ENDPOINT
        self.timeout = timeout

    def _post(self, query: str, variables: dict[str, Any], operation: str) -> dict[str, Any] | None:
        payload = {"query": query, "variables": variables, "operationName": operation}
        try:
            resp = requests.post(self.base_url, json=payload, timeout=self.timeout, verify=False)
            resp.raise_for_status()
            body = resp.json()
            if "errors" in body:
                logger.warning("GraphQL errors for %s/%s: %s", operation, variables, body["errors"])
            return body.get("data")
        except Exception as exc:
            logger.error("GraphQL call failed (%s, %s): %s", operation, variables, exc)
            return None

    def recent_ac_submissions(self, username: str, limit: int = 20) -> list[dict[str, Any]]:
        data = self._post(
            RECENT_AC_QUERY,
            {"username": username, "limit": limit},
            "recentAcSubmissions",
        )
        if not data:
            return []
        return data.get("recentAcSubmissionList") or []

    def user_profile(self, username: str) -> dict[str, Any]:
        """Fetch profile + problems-solved + calendar in parallel and merge."""
        result: dict[str, Any] = {}

        def pull_profile() -> None:
            data = self._post(USER_PROFILE_QUERY, {"username": username}, "userPublicProfile")
            if data:
                result["profile"] = data.get("matchedUser")

        def pull_solved() -> None:
            data = self._post(
                USER_PROBLEMS_SOLVED_QUERY, {"username": username}, "userProblemsSolved"
            )
            if data:
                result["solved"] = data

        def pull_calendar() -> None:
            data = self._post(
                USER_CALENDAR_QUERY,
                {"username": username, "year": None},
                "userProfileCalendar",
            )
            if data:
                result["calendar"] = (data.get("matchedUser") or {}).get("userCalendar")

        with ThreadPoolExecutor(max_workers=3) as pool:
            for fut in (pool.submit(pull_profile), pool.submit(pull_solved), pool.submit(pull_calendar)):
                fut.result()

        return result


if __name__ == "__main__":
    import json
    import sys

    logging.basicConfig(level=logging.INFO)
    if len(sys.argv) < 2:
        print("Usage: python leetcode_api.py <username> [US|CN]")
        sys.exit(1)
    user = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "US"
    client = LeetCodeClient(region)
    print(json.dumps(
        {
            "recent": client.recent_ac_submissions(user),
            "profile": client.user_profile(user),
        },
        indent=2,
    ))
