# AdventureWorks Analytics Engineering

A reliable, **reproducible** dimensional model over the AdventureWorks online-sales data
(**dbt-core + DuckDB**, fully offline), surfaced through an **Apache Superset** dashboard, that answers
the business questions in [`docs/CHALLENGE.md`](docs/CHALLENGE.md) and reconciles to the accounting audit
(2011 gross sales = **$12,646,112.16**).

- **Product truth:** [`docs/PRD.md`](docs/PRD.md) · **Technical truth:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Decisions:** [`docs/adrs/`](docs/adrs/) (ADR-0001 … ADR-0009)
- **Layering (medallion via dbt, ADR-0009):** `staging/` (Silver, views) · `intermediate/` (Silver,
  ephemeral) · `marts/` (Gold, tables)

## Prerequisites
- Python 3.11 or 3.12
- [`uv`](https://docs.astral.sh/uv/) (dependency manager)

## Setup & run
```bash
# 1. Install dbt-core + dbt-duckdb into a local venv
uv sync

# 2. Use the project-local profile (DuckDB, no cloud credentials)
export DBT_PROFILES_DIR=.

# 3. Install dbt packages, verify the connection, build everything
uv run dbt deps
uv run dbt debug          # -> All checks passed
uv run dbt build          # runs seeds -> models -> tests against ./adventureworks.duckdb

# Source-layer tests only (challenge demo):
uv run dbt test --select source:*
```

The DuckDB database is written to `./adventureworks.duckdb` (git-ignored). Everything runs offline; a
grader can reproduce every number with the commands above.

## Project status
Built via a Spec-Driven Development loop — see [`docs/PROGRESS.md`](docs/PROGRESS.md) for the current
phase and worklog, and [`docs/phases/`](docs/phases/) for per-phase plans and backlogs.
