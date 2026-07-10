# AdventureWorks Analytics Engineering

A reliable, **reproducible** dimensional model over the AdventureWorks online-sales data
(**dbt-core + DuckDB**, fully offline), surfaced through an **Apache Superset** dashboard, that answers
the business questions in [`docs/CHALLENGE.md`](docs/CHALLENGE.md) and reconciles to the accounting audit
(2011 gross sales = **$12,646,112.16**).

- **Product truth:** [`docs/PRD.md`](docs/PRD.md) · **Technical truth:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Decisions:** [`docs/adrs/`](docs/adrs/) (ADR-0001 … ADR-0009)
- **dbt project:** [`transform/`](transform/) · **EDA:** `notebooks/` · **BI (Superset):** `bi/`
- **Layering (medallion via dbt, ADR-0009):** `transform/models/staging` (Silver, views) ·
  `intermediate` (Silver, ephemeral) · `marts` (Gold, tables)

## Prerequisites
- Python 3.11 or 3.12
- [`uv`](https://docs.astral.sh/uv/) (dependency manager)
- [`just`](https://github.com/casey/just) — `uv tool install rust-just`

## Setup & run
```bash
just setup        # uv sync + dbt deps (installs dbt-core, dbt-duckdb, dev tools, dbt packages)
just debug        # dbt debug -> All checks passed
just build        # seeds -> models -> tests against a local DuckDB file (offline)
just test-source  # source-layer tests only (challenge demo)
just check        # lint + typecheck + build + tests (what CI would run)
```

The dbt project lives in [`transform/`](transform/); `just` runs dbt there with the project-local DuckDB
profile (no cloud credentials). The DuckDB database is git-ignored. Everything runs offline; a grader can
reproduce every number with `just build`. Raw dbt still works from `transform/` if you prefer.

## Project status
Built via a Spec-Driven Development loop — see [`docs/PROGRESS.md`](docs/PROGRESS.md) for the current
phase and worklog, and [`docs/phases/`](docs/phases/) for per-phase plans and backlogs.
