# Phase 1 — Foundation · Backlog

> Parent: [`docs/phases/phase-1/prd.md`](prd.md). Integration branch `develop`; each issue on
> `issue/<id>-<slug>`, auto-merge via gh PR. Statuses: `todo → doing → done`.
> Test command: `dbt build` · `dbt test --select source:*`.

| ID | Title | Status | Blocked by |
|----|-------|--------|-----------|
| P1-01 | dbt-core + DuckDB project scaffold | done (PR #1) | — |
| P1-02 | Seed `adventure_works` fixtures + declare source | todo | P1-01 |
| P1-03 | Source-layer tests green (`source:*`) | todo | P1-02 |

---

## P1-01 — dbt-core + DuckDB project scaffold

### Parent
`docs/phases/phase-1/prd.md` → realizes NFR-1, NFR-4.

### What to build
A runnable dbt-core project targeting a local DuckDB file, buildable fully offline. Includes
`dbt_project.yml`, a DuckDB `profiles.yml` (or `profiles.yml` template + env), and `packages.yml`
pinning `dbt_utils` and `dbt_expectations`. Folder structure follows ADR-0009 (staging/intermediate/marts
placeholders). After `dbt deps`, `dbt debug` passes and `dbt build` runs green on the empty project.
A README section documents how to install and run (NFR-4).

### Acceptance criteria
```gherkin
Scenario: The dbt project builds offline against local DuckDB
  Given a fresh checkout with dbt-core and the DuckDB adapter installed
  When I run "dbt deps" then "dbt debug" then "dbt build"
  Then dbt connects to a local DuckDB database with no cloud credentials
  And "dbt debug" reports all checks passed
  And "dbt build" completes green
```
- [ ] `packages.yml` pins `dbt_utils` and `dbt_expectations`; `dbt deps` installs them
- [ ] `staging/`, `intermediate/`, `marts/` folders scaffolded per ADR-0009
- [ ] README documents install + run steps (uv/pip, `dbt build`)

### Inner loop (TDD)
`skipped — pure project scaffolding/config; the Gherkin build scenario is the end-to-end gate, no unit-decomposable logic`

### Blocked by
None - can start immediately

---

## P1-02 — Seed `adventure_works` fixtures + declare source

### Parent
`docs/phases/phase-1/prd.md` → realizes NFR-1; Bronze layer + dbt-sources seam.

### What to build
Tiny CSV **seed** fixtures for the `adventure_works` tables the sales model needs (sales order header &
detail, customer, person, product, address, state/province, country/region, credit card, sales reason,
sales-order↔reason bridge, special offer). A handful of representative rows each — enough to exercise
staging and source tests offline, not the full dataset. A `_sources.yml` declares the `adventure_works`
source over those relations (the Bronze boundary seam). `dbt seed` loads them into DuckDB and they are
queryable via `source()`.

> Note: these seeds are **test fixtures** (profile: no live infra in tests). Loading the *full*
> `adventure_works` data for the 2011 reconciliation is a separate concern — see Phase-1 open question.

### Acceptance criteria
```gherkin
Scenario: adventure_works seeds load and are addressable as a dbt source
  Given the scaffolded dbt project and CSV seed fixtures for the adventure_works tables
  When I run "dbt seed"
  Then each seeded table is loaded into the local DuckDB
  And a model selecting from source('adventure_works', <table>) resolves against the seed
  And "dbt build" remains green
```
- [ ] `_sources.yml` declares every seeded `adventure_works` table used downstream
- [ ] Seed CSVs are minimal but cover the columns staging/tests need (incl. `OnlineOrderFlag`, discount, sales-reason bridge)

### Inner loop (TDD)
`skipped — declarative seeds + source declaration (data/config); the seed/build scenario is the gate`

### Blocked by
- P1-01

---

## P1-03 — Source-layer tests green (`source:*`)

### Parent
`docs/phases/phase-1/prd.md` → realizes the source-test slice of FR-4.

### What to build
Source-layer data tests on the declared `adventure_works` sources (the dbt-sources seam): `not_null` and
`unique` on natural keys, expected-column presence, and accepted-value / row-count sanity via
`dbt_expectations`. Documentation (`description:`) on the source tables/columns under test. Running
`dbt test --select source:*` is green.

### Acceptance criteria
```gherkin
Scenario: Source tests pass on the adventure_works sources
  Given the declared adventure_works sources loaded from seeds
  When I run "dbt test --select source:*"
  Then every source test passes
  And the run includes not_null and unique tests on the source natural keys
  And the tested source tables and key columns carry descriptions
```
- [ ] `not_null` + `unique` on source natural keys (order header/detail, customer, product, etc.)
- [ ] At least one `dbt_expectations` shape/row-count test on a core source table
- [ ] `description:` on tested source tables and key columns

### Inner loop (TDD)
`skipped — declarative dbt schema tests; the source:* test run is itself the acceptance gate`

### Blocked by
- P1-02
