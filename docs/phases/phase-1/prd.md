# Phase 1 — Foundation (dbt scaffold · sources · seeds · source tests)

> **Derived, internal — no separate human sign-off** (the root `PRD.md` + `ARCHITECTURE.md` are the only
> human-validated baselines). This is a **thin projection** of one epic: it **references** the baselines
> by requirement ID / seam and **must not duplicate** their Problem/Solution/architecture prose.

## Realizes (requirement IDs)
`NFR-1` (reproducible offline: dbt-core + DuckDB builds green), `NFR-4` (documented, version-controlled),
and the **source-test slice of `FR-4`** (source tests green — `dbt test --select source:*`). Establishes
the **Bronze layer** that every later phase's staging/marts depend on. No dimensions or fact are built here.

## Capabilities in scope
Root MoSCoW rows: *"Conformed dimensional model … "* (foundation only — the runnable dbt project + source
declarations), *"Source tests … all green"* (source layer), *"Model + column documentation"* (project +
source documentation scaffold). See root `PRD.md`.

## Seam(s) touched
**dbt sources** — `_sources.yml` over the `adventure_works` schema; `source:*` schema tests. This is the
Bronze boundary seam from `ARCHITECTURE.md` → *Seams* #1. Layering per
[ADR-0009](../../adrs/0009-medallion-via-dbt-layers.md); DuckDB target per the profile.

## Depends on
None — first phase.

## DoD gate (this phase)
- `dbt debug` passes; `dbt build` runs **green** against local DuckDB (empty of models is fine — seeds +
  sources only at this stage).
- `dbt seed` loads the tiny CSV fixtures for the `adventure_works` tables under test.
- `_sources.yml` declares the `adventure_works` source; `dbt test --select source:*` runs **green**.
- `dbt_utils` (+ `dbt_expectations`) installed via `packages.yml`; project builds offline, no cloud.
- Project committed to the repo (GitHub), with a README note on how to run it (`NFR-4`).

## Deferred to later phases
- All dimensions (`dim_*`), the bridge, and `fct_sales` → Phases 2–3.
- PK / relationship / reconciliation tests on models → Phases 2–3 (only *source* tests here).
- EDA notebook, Superset dashboard, KPIs → Phase 4 + manual/external artifacts.
