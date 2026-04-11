"""
One-shot helper: convert a plain-text dump of LeetCode problems into CSV.

Originally `static/parse.py` in the Django layout. Kept here for completeness
so the repository has a single home for all Python tooling. Not invoked by
the daily workflow.

Input format (one problem per 3 lines):

    1. Two Sum
    Easy
    49.8%

Usage:
    python scripts/parse_problems.py input.txt output.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def convert(input_path: Path, output_path: Path) -> int:
    lines = input_path.read_text(encoding="utf-8").splitlines()
    count = 0
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Problem ID", "Problem Name", "Difficulty", "Acceptance Rate"])
        for i in range(0, len(lines) - 2, 3):
            header = lines[i].strip()
            if ". " not in header:
                continue
            problem_number, problem_name = header.split(". ", 1)
            difficulty = lines[i + 1].strip()
            percentage = lines[i + 2].strip()
            writer.writerow([problem_number, problem_name, difficulty, percentage])
            count += 1
    return count


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: python scripts/parse_problems.py <input.txt> <output.csv>")
        return 1
    count = convert(Path(argv[1]), Path(argv[2]))
    print(f"Wrote {count} problems to {argv[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
