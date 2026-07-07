"""Capture GitHub Actions workflow runs into notebooks/data/real/github_actions_runs.csv.

This script reproduces the capture behind the case study's real CI dataset:
the 100 most recent workflow runs from each of 7 large OSS repositories,
fetched from the GitHub REST API (``GET /repos/{owner}/{repo}/actions/runs``,
``per_page=100``) and appended ONLY when the ``run_id`` is not already in the
CSV.

Capture history
---------------
- 2026-06-27 — the checked-in dataset: 700 runs (100 per repo) spanning
  roughly 2026-05-13 to 2026-06-27 depending on each repo's activity.

Append-only rationale
---------------------
The API pages through recent runs only; older runs eventually fall out of
cheap reach. The CSV is the historical record, so this script never modifies
or drops an existing row — it only appends runs it has not seen before.

Schema notes
------------
- ``duration_sec`` = (updated_at − run_started_at) in seconds, 1 decimal —
  a queue-free wall-clock proxy, since the API does not expose a completion
  timestamp directly.
- Timestamps are kept exactly as the API returns them (UTC, trailing Z).
- Unauthenticated requests are fine for the 7 calls this makes (60/hour
  limit); set the ``GITHUB_TOKEN`` environment variable to raise it.

Usage
-----
    python src/fetch_gh_actions.py --dry-run
    python src/fetch_gh_actions.py --repos pallets/flask,facebook/react
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

REPOS: list[str] = [
    "pallets/flask",
    "microsoft/TypeScript",
    "facebook/react",
    "vercel/next.js",
    "pytorch/pytorch",
    "withastro/astro",
    "anthropics/anthropic-sdk-python",
]

COLUMNS = [
    "repo",
    "run_id",
    "workflow_name",
    "status",
    "conclusion",
    "event",
    "head_branch",
    "created_at",
    "run_started_at",
    "updated_at",
    "duration_sec",
]

PER_PAGE = 100
SLEEP_BETWEEN_REPOS_S = 1.5
REQUEST_TIMEOUT_S = 30

CSV_PATH = (
    Path(__file__).resolve().parents[1]
    / "notebooks"
    / "data"
    / "real"
    / "github_actions_runs.csv"
)


def parse_iso(ts: str) -> datetime:
    """Parse a GitHub API ISO-8601 timestamp (trailing Z)."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fetch_runs(repo: str, session: requests.Session) -> list[dict]:
    """Fetch the most recent workflow runs for one repository."""
    url = f"https://api.github.com/repos/{repo}/actions/runs"
    response = session.get(url, params={"per_page": PER_PAGE}, timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    return response.json().get("workflow_runs", [])


def transform(repo: str, run: dict) -> dict[str, str]:
    """Map one workflow-run object to the dataset schema."""
    run_started_at = run.get("run_started_at") or ""
    updated_at = run.get("updated_at") or ""
    duration_sec = ""
    if run_started_at and updated_at:
        delta = parse_iso(updated_at) - parse_iso(run_started_at)
        duration_sec = f"{delta.total_seconds():.1f}"
    return {
        "repo": repo,
        "run_id": str(run.get("id", "")),
        "workflow_name": run.get("name") or "",
        "status": run.get("status") or "",
        "conclusion": run.get("conclusion") or "",
        "event": run.get("event") or "",
        "head_branch": run.get("head_branch") or "",
        "created_at": run.get("created_at") or "",
        "run_started_at": run_started_at,
        "updated_at": updated_at,
        "duration_sec": duration_sec,
    }


def load_existing_run_ids(csv_path: Path) -> set[str]:
    """Read the run_ids already present in the dataset."""
    if not csv_path.exists():
        return set()
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {row["run_id"] for row in csv.DictReader(fh)}


def append_rows(csv_path: Path, rows: list[dict[str, str]]) -> None:
    """Append new rows to the CSV without touching existing lines."""
    needs_leading_newline = False
    if csv_path.exists() and csv_path.stat().st_size > 0:
        with csv_path.open("rb") as fh:
            fh.seek(-1, 2)
            needs_leading_newline = fh.read(1) != b"\n"
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", newline="", encoding="utf-8") as fh:
        if needs_leading_newline:
            fh.write("\n")
        writer = csv.DictWriter(fh, fieldnames=COLUMNS)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="fetch and report what would be appended, but do not write the CSV",
    )
    parser.add_argument(
        "--repos",
        default=None,
        help="comma-separated owner/repo names to capture (default: the 7 tracked repos)",
    )
    args = parser.parse_args(argv)

    if args.repos:
        selected = [r.strip() for r in args.repos.split(",") if r.strip()]
        unknown = sorted(set(selected) - set(REPOS))
        if unknown:
            parser.error(f"unknown repos: {', '.join(unknown)} (known: {', '.join(REPOS)})")
    else:
        selected = list(REPOS)

    existing = load_existing_run_ids(CSV_PATH)
    print(f"dataset: {CSV_PATH}")
    print(f"existing rows: {len(existing)} unique run_ids")

    session = requests.Session()
    session.headers["Accept"] = "application/vnd.github+json"
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        session.headers["Authorization"] = f"Bearer {token}"

    new_rows: list[dict[str, str]] = []
    for i, repo in enumerate(selected):
        if i > 0:
            time.sleep(SLEEP_BETWEEN_REPOS_S)
        try:
            runs = fetch_runs(repo, session)
        except requests.RequestException as exc:
            print(f"  {repo:<34} FETCH FAILED ({exc}) — skipping, nothing lost")
            continue
        rows = [transform(repo, run) for run in runs]
        fresh = [r for r in rows if r["run_id"] not in existing]
        new_rows.extend(fresh)
        print(f"  {repo:<34} fetched {len(rows):>3}, new {len(fresh):>3}")

    print(f"total new rows: {len(new_rows)}")
    if args.dry_run:
        print("dry run — CSV not modified")
        return 0
    if new_rows:
        append_rows(CSV_PATH, new_rows)
        print(f"appended {len(new_rows)} rows to {CSV_PATH}")
    else:
        print("nothing to append")
    return 0


if __name__ == "__main__":
    sys.exit(main())
