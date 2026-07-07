# Where this data comes from, and how to check me

Every "real" claim in these notebooks rests on the three CSVs in this folder. This note exists so that nobody has to take the word *real* on faith: it states what each file is, which public endpoint produced it, when, under what transformation, and how to re-run the capture yourself. Where the data has a quirk that could mislead an analysis, I say so here rather than hoping a footnote in a notebook catches it.

## The three files

| File | Rows | What it is |
|---|---|---|
| `service_incidents.csv` | 787 incidents, 18 providers | Public status-page incidents, captured in two phases (2026-06-27 and 2026-07-03) |
| `github_actions_runs.csv` | 700 runs, 7 repos | GitHub Actions workflow runs, captured 2026-06-27 |
| `staging_service_incidents_expansion.csv` | 684 incidents, 15 providers | The 2026-07-03 expansion capture, kept standalone (see below) |

## The incident capture

Seventeen of the eighteen providers publish an Atlassian Statuspage v2 API: `https://<statuspage-domain>/api/v2/incidents.json`, which returns roughly the last 50 incidents and requires a browser-like User-Agent. The capture happened in two phases. On 2026-06-27 I captured github (www.githubstatus.com), claude_anthropic (status.anthropic.com), and gcp. On 2026-07-03 I expanded to fifteen more: cloudflare (www.cloudflarestatus.com), vercel (www.vercel-status.com), npm (status.npmjs.org), datadog (status.datadoghq.com), twilio (status.twilio.com), dropbox (status.dropbox.com), discord (discordstatus.com), linear (linearstatus.com), atlassian (status.atlassian.com), reddit (redditstatus.com), openai (status.openai.com), digitalocean (status.digitalocean.com), circleci (status.circleci.com), zoom (status.zoom.us), and figma (status.figma.com). Some providers I wanted and could not have: Stripe, PagerDuty, and Notion expose no public v2 API, and Slack and Heroku use proprietary formats I judged not worth an adapter.

Two fields are derived; everything else is passed through as the API returned it. `duration_min` is (resolved_at − created_at) in minutes, one decimal, empty while an incident is unresolved (13 rows). `affected_components` is the pipe-joined list of component names.

`staging_service_incidents_expansion.csv` is the raw output of the 2026-07-03 phase, before it was appended to the combined file. I keep it because it is the audit artifact for the expansion: anyone can verify that the combined dataset equals the 2026-06-27 capture plus this file, row for row.

## The `impact` field is the settled value, not the minute-0 declaration

This is the one semantic that can silently wreck an analysis, so it gets its own section. Statuspage returns the impact *in force at fetch time*. Status pages routinely upgrade impact while an incident unfolds (minor becomes major becomes critical), and a single snapshot cannot recover what the label said at minute 0. For every resolved incident in this file, `impact` is therefore the final, settled severity — a label that partially already knows how the incident ended. Any model that feeds `impact` to a "predict at minute 0" question is leaking the outcome into the features, which is exactly why NB04 treats the with-impact model as a declared optimistic ceiling and the without-impact model as the honest estimate. If you reuse this data, I'd invite you to inherit that treatment rather than rediscover the leak.

## Observation windows are not comparable across providers

Because the API returns the last ~50 incidents regardless of how long those took to accumulate, each provider's window is a different slice of history: Twilio's 50 incidents span 8 days (one crisis, essentially), while Atlassian's 34 span almost six years — a ratio of roughly 256×. Any rate, availability figure, or cross-provider comparison must be computed strictly inside each provider's own window; pooling calendar time across providers manufactures nonsense. The notebooks do this, and so should any reuse.

## Two special cases

The gcp rows are three incident identifiers and nothing else. Google's status page (status.cloud.google.com) is not a Statuspage v2 API; those rows came from a separate manual capture of its custom format, and only the IDs were mapped. They are inert in every duration and impact analysis, and the capture script deliberately does not handle GCP.

OpenAI's API omits the `components` and `shortlink` fields, so `affected_components` and `shortlink` are empty for all 25 openai rows. That is a property of their endpoint, not missing data on my side.

## The CI runs capture

`github_actions_runs.csv` holds the 100 most recent workflow runs from each of 7 large OSS repositories (pallets/flask, microsoft/TypeScript, facebook/react, vercel/next.js, pytorch/pytorch, withastro/astro, anthropics/anthropic-sdk-python), fetched on 2026-06-27 from the GitHub REST API (`GET /repos/{owner}/{repo}/actions/runs`, `per_page=100`). The window that "100 recent runs" buys differs by repo activity; overall the file spans 2026-05-13 to 2026-06-27. The derived field is `duration_sec` = (updated_at − run_started_at) in seconds, one decimal. The same window caveat applies, and one more that I state plainly: seven large OSS repos say nothing about your monorepo.

## Re-running the capture

Both captures are reproducible with the scripts in `../../../src/`:

```bash
python src/capture_status_pages.py --dry-run   # report what a fresh fetch would add
python src/capture_status_pages.py             # append new incidents
python src/fetch_gh_actions.py --dry-run
python src/fetch_gh_actions.py
```

Both scripts are append-only by design: they deduplicate on (provider, incident_id) and run_id respectively, and they never modify or drop an existing row. The reason is not caution for its own sake — status pages age out old incidents, so a fresh fetch can never recover what these files already hold. The CSVs are the only historical record, and the scripts treat them that way. One warning if you do refresh: the notebooks are not re-executed automatically, so the numbers in their prose reflect the capture they ran on.
