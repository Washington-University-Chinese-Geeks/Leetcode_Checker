"""
JSON schema validator for data/ artifacts.

Validates `data/users/*.json` against `scripts/schemas/user.schema.json` and
`data/summary.json` against `scripts/schemas/summary.schema.json`. The
collector invokes this before committing; it can also be run standalone as a
CI check:

    python scripts/validator.py                 # validate everything under data/
    python scripts/validator.py data/users/foo.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator, RefResolver
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "jsonschema is required: pip install -r scripts/requirements.txt"
    ) from exc

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
DATA_DIR = ROOT / "data"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _build_validator(schema_name: str) -> Draft202012Validator:
    """Build a validator that can resolve sibling `$ref`s inside SCHEMA_DIR."""
    schema_path = SCHEMA_DIR / schema_name
    schema = _load_json(schema_path)
    base_uri = schema_path.parent.as_uri() + "/"
    # Preload every sibling schema into the resolver store so that relative
    # $refs resolve locally even when a schema's own $id is a remote URL.
    # Without this, jsonschema tries to HTTP-fetch the referenced schema and
    # explodes on the HTML 404 body.
    store: dict[str, Any] = {}
    for sibling in SCHEMA_DIR.glob("*.schema.json"):
        doc = _load_json(sibling)
        sid = doc.get("$id")
        if sid:
            store[sid] = doc
        store[base_uri + sibling.name] = doc
    resolver = RefResolver(base_uri=base_uri, referrer=schema, store=store)
    return Draft202012Validator(schema, resolver=resolver)


USER_VALIDATOR = _build_validator("user.schema.json")
SUMMARY_VALIDATOR = _build_validator("summary.schema.json")


def validate_user(payload: dict[str, Any]) -> list[str]:
    return [err.message for err in USER_VALIDATOR.iter_errors(payload)]


def validate_summary(payload: dict[str, Any]) -> list[str]:
    return [err.message for err in SUMMARY_VALIDATOR.iter_errors(payload)]


def validate_file(path: Path) -> tuple[bool, list[str]]:
    payload = _load_json(path)
    try:
        rel = path.relative_to(ROOT).as_posix()
    except ValueError:
        rel = path.as_posix()
    if rel.endswith("summary.json"):
        errors = validate_summary(payload)
    elif "users/" in rel or "users\\" in rel:
        errors = validate_user(payload)
    else:
        return True, []  # unknown file, skip
    return not errors, errors


def validate_tree(data_dir: Path = DATA_DIR) -> int:
    failures = 0
    targets: list[Path] = []
    summary = data_dir / "summary.json"
    if summary.exists():
        targets.append(summary)
    users_dir = data_dir / "users"
    if users_dir.exists():
        targets.extend(sorted(users_dir.glob("*.json")))

    if not targets:
        logger.warning("No data files found under %s", data_dir)
        return 0

    for path in targets:
        ok, errors = validate_file(path)
        if ok:
            logger.info("OK  %s", path)
        else:
            failures += 1
            logger.error("BAD %s", path)
            for err in errors:
                logger.error("    - %s", err)
    return failures


def main(argv: list[str]) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    if len(argv) == 1:
        return 1 if validate_tree() else 0
    failures = 0
    for arg in argv[1:]:
        ok, errors = validate_file(Path(arg))
        if ok:
            logger.info("OK  %s", arg)
        else:
            failures += 1
            logger.error("BAD %s", arg)
            for err in errors:
                logger.error("    - %s", err)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
