# ADR 001: Orchestrator Choice — Prefect over Airflow

**Status:** Accepted
**Date:** 2026-03-24
**Context:** We need an orchestrator for the legislative data pipeline.

## Options considered

### Apache Airflow
- **Pro:** Industry standard. Huge ecosystem of operators and providers.
- **Pro:** Permanent scheduler daemon — ideal for mission-critical 24/7 pipelines.
- **Con:** Significant operational overhead: database (PostgreSQL), webserver, scheduler, workers. Excessive for a personal portfolio.
- **Con:** DSL based on declarative DAGs. Complex logic requires workarounds.
- **Con:** DAG testing is notoriously difficult.

### Prefect
- **Pro:** Purely Pythonic API — flows and tasks are decorated Python functions.
- **Pro:** Zero infrastructure for local development: `python flow.py` runs the pipeline.
- **Pro:** Retries, caching, and logging built in with no extra configuration.
- **Pro:** Prefect Cloud offers a free tier for monitoring (optional).
- **Con:** Lower adoption than Airflow in Fortune 500 companies.

### Dagster
- **Pro:** The software-defined-assets paradigm is elegant for modeling dependencies.
- **Pro:** Excellent development UI (Dagit).
- **Con:** Steeper learning curve. Concepts like IOManagers and Resources add upfront complexity.
- **Con:** Smaller community than Prefect for troubleshooting.

## Decision

**Prefect** as the primary orchestrator.

## Justification

For a portfolio project that must be:
1. **Locally runnable** with no Docker or auxiliary databases
2. **Readable** by reviewers unfamiliar with the framework
3. **Testable** with standard pytest

Prefect offers the best signal-to-noise ratio. The full pipeline runs with
`python flows/legislative_pipeline.py`. No daemon to maintain, no UI to
deploy, no metadata database to migrate.

In an enterprise environment with multiple pipelines and SLAs, Airflow would
be the right call. To demonstrate orchestration competence with minimum
overhead, Prefect wins.

## Consequences

- Flows are pure Python functions: portable to any future orchestrator.
- If the project migrates to production with Airflow, the refactor is
  mechanical (decorators → DAG operators).
- Native cron-based scheduling (Airflow) is lost; compensated via Prefect
  schedules or system cron.
