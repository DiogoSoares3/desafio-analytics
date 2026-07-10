# analytics-exam — AdventureWorks Analytics Engineering

Analytics-engineering certification challenge. Build a reliable dimensional model over the
AdventureWorks dataset (dbt + tests), an EDA, a conceptual DW diagram, KPIs, and a BI dashboard that
answers the business questions in [`docs/CHALLENGE.md`](docs/CHALLENGE.md).

**Stack:** dbt-core + DuckDB (local, offline) → Apache Superset (BI-as-code). Python is a thin layer
(EDA notebook, any Superset/helper scripts); the bulk of the codebase is SQL + YAML.

> This file holds **static project conventions** only. Product/technical truth lives in
> [`docs/PRD.md`](docs/PRD.md) and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md); closed decisions in
> [`docs/adrs/`](docs/adrs/). How to run things: the `justfile` and [`README.md`](README.md).

## Golden rule
**Reproducible offline.** Every number must reconcile to source and a grader must re-run the whole
pipeline with no cloud credentials and get the same result (`just build` against local DuckDB). When
correctness/reproducibility conflicts with convenience, reproducibility wins.

## Toolchain
Single entrypoint is the **`justfile`** — prefer `just <recipe>` over raw commands.

| Tool | Role | Invoked by |
|---|---|---|
| **uv** | Python env + dependency manager (installs dbt, dev tools) | `uv sync`, `uv run …` |
| **just** | Task runner / single entrypoint | `just`, `just build`, `just lint` |
| **ruff** | Python lint + format | `just lint` / `just fmt` (`.py` only) |
| **pyright** | Python type check (mode: `standard`) | `just typecheck` |
| **sqlfluff** | SQL lint + format for dbt models (dbt templater, DuckDB dialect) | `just lint` / `just fmt` |
| **commitizen** | Conventional-commit authoring + validation | `just commit`, commit-msg hook |
| **prek** | Git hook runner (reads `.pre-commit-config.yaml`) | `prek install`, runs on commit |

Install prerequisites once: `uv sync` (Python deps), `uv tool install rust-just` (the `just` binary),
`prek install` (git hooks). See [`README.md`](README.md).

## Repository layout
```
transform/                    # the dbt project (self-contained)
  dbt_project.yml  packages.yml  profiles.yml
  models/
    staging/                  # Silver — stg_adventure_works__*  (views)
    intermediate/             # Silver — int_*                   (ephemeral)
    marts/                    # Gold   — dim_* / fct_* / bridge_* (tables)
  seeds/                      # tiny CSV test fixtures (no live infra in tests)
  tests/                      # singular (reconciliation) tests
  macros/                     # reusable SQL
notebooks/                    # EDA (Python)
bi/                           # Apache Superset BI-as-code (YAML exports)
data/                         # local DuckDB + raw exports (git-ignored, shared by dbt & notebooks)
docs/                         # PRD, ARCHITECTURE, ADRs, CHALLENGE, phases, diagrams
pyproject.toml  uv.lock       # Python env (shared by dbt + notebooks)
justfile  README.md  CLAUDE.md
```
Run dbt via `just` (it targets `transform/`); avoid calling dbt raw unless debugging.
Layering follows the medallion mapping in [ADR-0009](docs/adrs/0009-medallion-via-dbt-layers.md).

## dbt / SQL conventions
- **Model naming:** staging `stg_adventure_works__<entity>`; intermediate `int_<entity>__<transform>`;
  marts `dim_<entity>`, `fct_<process>`, `bridge_<a>_<b>`. One entity per staging model, 1:1 with source.
- **Materialization** is set per layer in `dbt_project.yml` (staging=view, intermediate=ephemeral,
  marts=table) — do not override per-model without a reason noted in the model.
- **Keys:** surrogate PKs named `<entity>_key`, generated with `dbt_utils.generate_surrogate_key`
  ([ADR-0007](docs/adrs/0007-surrogate-keys.md)). Fact carries dim `_key` FKs + degenerate identifiers.
- **References:** always `ref()` / `source()` — never hardcode schema/table names. Raw access only
  through declared sources (`_sources.yml`).
- **SQL style (enforced by sqlfluff):** lowercase keywords, `snake_case` identifiers, trailing commas,
  CTEs over nested subqueries, leading CTE named `with … as (…)`. Import CTEs (`ref`/`source`) at the top.
- **Documentation is not optional:** every mart model and column carries a `description:` in its
  `_*.yml` (grading + `NFR-4`). Undocumented mart columns fail review.
- **Tests live with the model:** PK `unique`+`not_null` on every dim/fact, `relationships` on FKs,
  `accepted_values` on domains; reconciliation/invariants as singular tests in `tests/`. Fixtures are
  seeds. The green signal is `just build` (`dbt build`) and `just test-source` (`dbt test --select source:*`).

## Python conventions
- Python is minimal (EDA, helper scripts). Keep it that way — modeling belongs in dbt/SQL, not pandas.
- **ruff** governs lint + format (line length 100, default rule set). Run `just fmt` before committing.
- **pyright** in `standard` mode; add type hints to any non-notebook module. Notebooks are exempt from
  pyright but not from ruff where practical.

## Commit conventions
**Conventional Commits**, authored/validated with **commitizen**, one issue id, and the agent trailer:

```
<type>(<scope>): <subject> [<issue-id>]

<body — what & why>
```

- `type` ∈ `feat｜fix｜docs｜chore｜refactor｜test｜build｜ci`. `scope` is the area
  (`dims`, `fact`, `staging`, `sources`, `dbt`, `bi`, `docs`). Example:
  `feat(dims): add dim_product with PK tests [P2-01]`.
- Prefer `just commit` (commitizen prompt). The commit-msg hook (prek) rejects non-conforming messages.
- One logical change per commit; keep the tree green (`just check`) before committing.
