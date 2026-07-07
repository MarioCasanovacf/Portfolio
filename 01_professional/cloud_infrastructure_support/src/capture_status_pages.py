"""Capture public status-page incidents into notebooks/data/real/service_incidents.csv.

This script reproduces the capture behind the case study's real incident dataset.
It fetches each provider's Statuspage v2 endpoint
(``https://<domain>/api/v2/incidents.json``, which returns roughly the last 50
incidents and requires a browser-like User-Agent), transforms the payload to the
dataset schema, and appends ONLY incidents whose ``(provider, incident_id)`` pair
is not already in the CSV.

Capture history
---------------
- 2026-06-27 — initial capture: github, claude_anthropic, gcp.
- 2026-07-03 — expansion: cloudflare, vercel, npm, datadog, twilio, dropbox,
  discord, linear, atlassian, reddit, openai, digitalocean, circleci, zoom,
  figma. The expansion also exists standalone as
  ``staging_service_incidents_expansion.csv`` in the same folder.

Append-only rationale
---------------------
Status pages age out old incidents: a fresh fetch returns only the most recent
~50, so re-fetching can never recover what was captured before. The CSV is
therefore the only historical record, and this script never modifies or drops
an existing row — it only appends new ones.

Schema notes
------------
- ``duration_min`` = (resolved_at − created_at) in minutes, 1 decimal, empty
  while the incident is unresolved.
- ``affected_components`` = pipe-joined component names.
- ``impact`` is the value AT FETCH TIME. For resolved incidents that is the
  settled/final impact, not the minute-0 declaration (NB04 depends on this
  semantic).
- OpenAI's API lacks the ``components`` and ``shortlink`` fields; those columns
  stay empty for that provider.
- GCP is NOT handled here: status.cloud.google.com uses a custom (non-
  Statuspage) format and its 3 rows were captured separately.
- Rejected providers: Stripe, PagerDuty, Notion (no public v2 API); Slack and
  Heroku (proprietary formats).

Usage
-----
    python src/capture_status_pages.py --dry-run
    python src/capture_status_pages.py --providers github,cloudflare
"""

from __future__ import annotations

import argparse
import csv
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

# provider slug -> status page domain (Statuspage v2 API)
PROVIDERS: dict[str, str] = {
    "github": "www.githubstatus.com",
    "claude_anthropic": "status.anthropic.com",
    "cloudflare": "www.cloudflarestatus.com",
    "vercel": "www.vercel-status.com",
    "npm": "status.npmjs.org",
    "datadog": "status.datadoghq.com",
    "twilio": "status.twilio.com",
    "dropbox": "status.dropbox.com",
    "discord": "discordstatus.com",
    "linear": "linearstatus.com",
    "atlassian": "status.atlassian.com",
    "reddit": "redditstatus.com",
    "openai": "status.openai.com",
    "digitalocean": "status.digitalocean.com",
    "circleci": "status.circleci.com",
    "zoom": "status.zoom.us",
    "figma": "status.figma.com",
}

COLUMNS = [
    "provider",
    "incident_id",
    "name",
    "impact",
    "status",
    "created_at",
    "resolved_at",
    "duration_min",
    "affected_components",
    "shortlink",
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
SLEEP_BETWEEN_PROVIDERS_S = 1.5
REQUEST_TIMEOUT_S = 30

CSV_PATH = (
    Path(__file__).resolve().parents[1] / "notebooks" / "data" / "real" / "service_incidents.csv"
)


def parse_iso(ts: str) -> datetime:
    """Parse a Statuspage ISO-8601 timestamp (trailing Z, with or without millis)."""
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def fetch_incidents(domain: str, session: requests.Session) -> list[dict]:
    """Fetch the incident list from a provider's Statuspage v2 API."""
    url = f"https://{domain}/api/v2/incidents.json"
    response = session.get(url, timeout=REQUEST_TIMEOUT_S)
    response.raise_for_status()
    return response.json().get("incidents", [])


def transform(provider: str, incident: dict) -> dict[str, str]:
    """Map one Statuspage incident object to the dataset schema.

    Timestamps are kept exactly as the API returns them (formats vary slightly
    across providers, e.g. with/without milliseconds).
    """
    created_at = incident.get("created_at") or ""
    resolved_at = incident.get("resolved_at") or ""
    duration_min = ""
    if created_at and resolved_at:
        delta = parse_iso(resolved_at) - parse_iso(created_at)
        duration_min = f"{delta.total_seconds() / 60:.1f}"
    components = incident.get("components") or []
    return {
        "provider": provider,
        "incident_id": incident.get("id", ""),
        "name": incident.get("name", ""),
        "impact": incident.get("impact", ""),
        "status": incident.get("status", ""),
        "created_at": created_at,
        "resolved_at": resolved_at,
        "duration_min": duration_min,
        "affected_components": "|".join(c.get("name", "") for c in components),
        "shortlink": incident.get("shortlink") or "",
    }


def load_existing_keys(csv_path: Path) -> set[tuple[str, str]]:
    """Read the (provider, incident_id) pairs already present in the dataset."""
    if not csv_path.exists():
        return set()
    with csv_path.open(newline="", encoding="utf-8") as fh:
        return {(row["provider"], row["incident_id"]) for row in csv.DictReader(fh)}


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
        "--providers",
        default=None,
        help="comma-separated provider slugs to capture (default: all "
        f"{len(PROVIDERS)} Statuspage providers)",
    )
    args = parser.parse_args(argv)

    if args.providers:
        selected = [p.strip() for p in args.providers.split(",") if p.strip()]
        unknown = sorted(set(selected) - set(PROVIDERS))
        if unknown:
            parser.error(f"unknown providers: {', '.join(unknown)} "
                         f"(known: {', '.join(sorted(PROVIDERS))})")
    else:
        selected = list(PROVIDERS)

    existing = load_existing_keys(CSV_PATH)
    print(f"dataset: {CSV_PATH}")
    print(f"existing rows: {len(existing)} unique (provider, incident_id) pairs")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    new_rows: list[dict[str, str]] = []
    for i, provider in enumerate(selected):
        if i > 0:
            time.sleep(SLEEP_BETWEEN_PROVIDERS_S)
        domain = PROVIDERS[provider]
        try:
            incidents = fetch_incidents(domain, session)
        except requests.RequestException as exc:
            print(f"  {provider:<18} FETCH FAILED ({exc}) — skipping, nothing lost")
            continue
        rows = [transform(provider, inc) for inc in incidents]
        fresh = [r for r in rows if (r["provider"], r["incident_id"]) not in existing]
        new_rows.extend(fresh)
        print(f"  {provider:<18} fetched {len(rows):>3}, new {len(fresh):>3}")

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
