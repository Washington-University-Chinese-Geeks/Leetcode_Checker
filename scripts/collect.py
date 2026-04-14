"""
Daily collector entry point.

Flow (driven by .github/workflows/collect.yml):

    1. Read the member roster from Google Sheets via GoogleSheetClient.
    2. For each member, call the LeetCode GraphQL API to pull recent AC
       submissions and public profile stats.
    3. Write one JSON file per user to `data/users/<slug>.json` and a
       top-level `data/summary.json`.
    4. Validate every written file against the schemas in
       `scripts/schemas/`. Fail the run if anything is malformed.

The script is intentionally idempotent: running it twice on the same day
produces byte-identical output if nothing has changed upstream, so git will
report no diff and the workflow will skip the commit.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from google_sheet import GoogleSheetClient, Member
from leetcode_api import LeetCodeClient
from validator import validate_summary, validate_user

logger = logging.getLogger("collect")

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
USERS_DIR = DATA_DIR / "users"

SAFE_SLUG = re.compile(r"[^a-z0-9._-]+")


def slugify(value: str) -> str:
    """Filesystem-safe slug for user JSON filenames."""
    return SAFE_SLUG.sub("-", value.strip().lower()).strip("-") or "unknown"


def _iso_from_timestamp(ts: str | int | None) -> str | None:
    if ts is None or ts == "":
        return None
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).isoformat()
    except (ValueError, OSError):
        return None


def _normalize_submission(raw: dict[str, Any]) -> dict[str, Any]:
    sid = str(raw.get("id") or "")
    slug = raw.get("titleSlug") or ""
    submission: dict[str, Any] = {
        "id": sid,
        "title": raw.get("title") or "",
        "title_slug": slug,
        "timestamp": str(raw.get("timestamp") or ""),
    }
    if sid:
        submission["proof_url"] = f"https://leetcode.com/submissions/detail/{sid}/"
    submitted_at = _iso_from_timestamp(raw.get("timestamp"))
    if submitted_at:
        submission["submitted_at"] = submitted_at
    return submission


def _extract_totals(solved_payload: dict[str, Any] | None) -> dict[str, int | None] | None:
    if not solved_payload:
        return None
    matched = solved_payload.get("matchedUser") or {}
    stats = (matched.get("submitStatsGlobal") or {}).get("acSubmissionNum") or []
    buckets = {"Easy": "easy", "Medium": "medium", "Hard": "hard", "All": "all"}
    out: dict[str, int | None] = {"easy": None, "medium": None, "hard": None, "all": None}
    for row in stats:
        key = buckets.get(row.get("difficulty"))
        if key:
            out[key] = row.get("count")
    return out


def _extract_profile(profile_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not profile_payload:
        return None
    profile = profile_payload.get("profile") or {}
    return {
        "ranking": profile.get("ranking"),
        "user_avatar": profile.get("userAvatar"),
        "real_name": profile.get("realName"),
        "country_name": profile.get("countryName"),
        "reputation": profile.get("reputation"),
    }


def _extract_calendar(calendar_payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not calendar_payload:
        return None
    return {
        "streak": calendar_payload.get("streak"),
        "total_active_days": calendar_payload.get("totalActiveDays"),
        "submission_calendar": calendar_payload.get("submissionCalendar"),
    }


def _parse_plan_date(raw: str) -> date | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _sum_calendar_in_range(
    calendar_json: str | None,
    start: date,
    end: date,
) -> int:
    """Sum daily AC counts from LeetCode's submissionCalendar JSON string."""
    if not calendar_json:
        return 0
    try:
        buckets = json.loads(calendar_json)
    except (TypeError, ValueError):
        return 0
    total = 0
    for epoch_str, count in buckets.items():
        try:
            day = datetime.fromtimestamp(int(epoch_str), tz=timezone.utc).date()
        except (TypeError, ValueError, OSError):
            continue
        if start <= day <= end:
            total += int(count)
    return total


def _build_plan(
    member: Member,
    calendar_payload: dict[str, Any] | None,
    today: date,
) -> dict[str, Any] | None:
    """Compute the plan window and AC count within it."""
    start = _parse_plan_date(member.start_date)
    if start is None:
        return None
    expire = _parse_plan_date(member.expire_date)
    # Cap the window at today: future end dates shouldn't be counted as past.
    window_end = min(expire, today) if expire else today
    if window_end < start:
        window_end = start
    calendar_json = (calendar_payload or {}).get("submissionCalendar")
    count = _sum_calendar_in_range(calendar_json, start, window_end)
    return {
        "start_date": start.isoformat(),
        "end_date": expire.isoformat() if expire else None,
        "submissions_in_period": count,
    }


def build_user_record(
    member: Member,
    leetcode: LeetCodeClient,
    *,
    now: datetime,
) -> dict[str, Any]:
    """Call LeetCode and shape the response into our on-disk JSON schema."""
    recent_raw = leetcode.recent_ac_submissions(member.leetcode_username)
    profile_bundle = leetcode.user_profile(member.leetcode_username)

    calendar = _extract_calendar(profile_bundle.get("calendar"))
    record: dict[str, Any] = {
        "leetcode_username": member.leetcode_username,
        "display_name": member.display_name,
        "server_region": member.server_region,
        "last_updated": now.isoformat(),
        "profile": _extract_profile(profile_bundle.get("profile")),
        "totals": _extract_totals(profile_bundle.get("solved")),
        "calendar": calendar,
        "plan": _build_plan(member, calendar, now.date()),
        "recent_submissions": [_normalize_submission(s) for s in recent_raw],
    }
    return record


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys + trailing newline keeps diffs minimal across runs
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def run(*, dry_run: bool = False) -> int:
    now = datetime.now(tz=timezone.utc)
    sheet = GoogleSheetClient.from_env()
    members = sheet.fetch_members()
    logger.info("Fetched %d members from Google Sheet", len(members))

    clients = {
        "US": LeetCodeClient("US"),
        "CN": LeetCodeClient("CN"),
    }

    summary_entries: list[dict[str, Any]] = []
    failures: list[str] = []

    # Dedupe: a member may appear in multiple sheet rows (schedules). The
    # user JSON is keyed on leetcode_username, so we only scrape once per user.
    seen: dict[str, Member] = {}
    for member in members:
        if not member.leetcode_username:
            continue
        seen.setdefault(member.leetcode_username.lower(), member)

    for member in seen.values():
        client = clients.get(member.server_region, clients["US"])
        logger.info(
            "Collecting %s (%s, region=%s)",
            member.leetcode_username,
            member.display_name,
            member.server_region,
        )
        try:
            record = build_user_record(member, client, now=now)
        except Exception as exc:
            logger.exception("Failed to collect %s: %s", member.leetcode_username, exc)
            failures.append(member.leetcode_username)
            continue

        errors = validate_user(record)
        if errors:
            logger.error(
                "Schema errors for %s: %s", member.leetcode_username, "; ".join(errors)
            )
            failures.append(member.leetcode_username)
            continue

        slug = slugify(member.leetcode_username)
        user_path = USERS_DIR / f"{slug}.json"
        if not dry_run:
            write_json(user_path, record)

        totals = record.get("totals") or {}
        most_recent = record["recent_submissions"][0] if record["recent_submissions"] else None
        plan = record.get("plan")
        summary_entries.append(
            {
                "leetcode_username": member.leetcode_username,
                "display_name": member.display_name,
                "server_region": member.server_region,
                "data_file": user_path.relative_to(ROOT).as_posix(),
                "total_solved": totals.get("all"),
                "recent_submission_count": len(record["recent_submissions"]),
                "last_submission_at": (most_recent or {}).get("submitted_at"),
                "plan_start_date": (plan or {}).get("start_date"),
                "plan_end_date": (plan or {}).get("end_date"),
                "plan_submission_count": (plan or {}).get("submissions_in_period"),
            }
        )

    summary_entries.sort(key=lambda e: e["leetcode_username"].lower())
    summary = {
        "generated_at": now.isoformat(),
        "member_count": len(summary_entries),
        "members": summary_entries,
    }
    errors = validate_summary(summary)
    if errors:
        logger.error("Summary failed schema validation: %s", "; ".join(errors))
        return 2

    if not dry_run:
        write_json(DATA_DIR / "summary.json", summary)

    if failures:
        logger.error("Collection finished with %d failures: %s", len(failures), failures)
        return 1
    logger.info("Collection complete: %d members written", len(summary_entries))
    return 0


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="Collect LeetCode submissions for the roster.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate but do not write any files.",
    )
    args = parser.parse_args()
    return run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
