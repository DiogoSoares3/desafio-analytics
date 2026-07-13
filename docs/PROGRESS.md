# PROGRESS — AdventureWorks Analytics Engineering

> **Durable loop state. Lives in the repo (never temp).** The single dynamic file — update it per
> completed slice. Static conventions/decisions go in the sources of truth, not here.
> Priming read order: `.sdd/profile.md` → **this file** → latest handoff (below) →
> `PRD.md` / `ARCHITECTURE.md` as needed.

## Current status
**Phase 3 (Fact + reconciliation) IN PROGRESS.** P3-01 **done + supervisor-verified** (PR #11): canonical
AdventureWorks loaded to committed `data/adventure_works/*.parquet`, source repointed via `read_parquet`,
`dbt build` PASS=99 on real data. I independently confirmed **2011 all-sales gross = $12,646,112.16**.

P3-02 **done** (PR #12): `stg_adventure_works__salesorderheadersalesreason` + `bridge_order_sales_reason`
mart at grain order × sales reason (ADR-0003) — resolves `sales_order_number` to `sales_reason_key`; the
base fact carries no reason FK, so gross never fans out. `dbt build` PASS=105 on real data (+4 tests:
`unique_combination_of_columns` on the grain, 2× `not_null`, `relationships` to `dim_sales_reason`).
`dbt test --select source:*` PASS=40. Inner loop was `skipped` per the issue — outer schema tests were
the gate. RED proven via `dbt build --select bridge_order_sales_reason` → "does not match any enabled
nodes" before the model existed; re-verified green from a clean checkout.

**SCOPE AMENDED (2026-07-11): all channels, not online-only.** P3-01 proved the audited figure is all-sales
(online-only = $3.86M, does not reconcile). PRD + ADR-0001 + ARCHITECTURE amended; **ADR-0010** records it.
Cascade: `fct_sales` covers online+reseller with `is_online` filter; **P3-05** added to rework `dim_customer`
(+stores) and `dim_credit_card` (+"N/A" member) before P3-03. ADRs now 0001–0010. Profile knobs:
auto-merge · handoff=auto · subagent-per-phase (worktree) · verifier on.

**Next:** dispatch Phase-3 worker(s) — P3-05 → P3-03 (fct, all channels) → P3-04 (recon). P3-02 done.

## Tactical decisions (reversible; recorded here, not ADRs)
- **Data = canonical public Microsoft AdventureWorks; DuckDB-only (no Postgres).** The ERD is the stock
  AW 2008 OLTP schema and `$12,646,112.16` is the well-known AW figure, so the challenge data is the
  public MS sample — a download, not the user's DB. P3-01 loads the in-scope tables straight into DuckDB
  and commits `data/adventure_works/*.parquet` (offline source-of-record); dbt reads them via
  `external_location` (`read_parquet`), so `source()` + staging stay verbatim. **No Postgres, no
  docker-compose, no ADR** — Postgres was a wrong turn (the challenge only *describes* a pg source; our
  warehouse is DuckDB by ADR-0002/0009).
- ⚠️ **Date-shift caveat:** the *current* MS CSV release shifts OrderDate to ~2022+ (no 2011). P3-01 must
  source a fixed-date (2011–2014) AdventureWorks; the 2011 reconciliation is the oracle for the right set.

## In review (PR open, awaiting merge) — n/a under auto-merge
_Empty: auto-merge lands issues straight to `done`._

## Latest handoff
_none — Phase 2 closed at a clean boundary; files describe the position._

## Next actions
1. Phase-3 backlog **approved** (confirm gate passed).
2. P3-01 done, P3-02 done. **Dispatch P3-05** (all-channel dim rework) next — it must land before
   P3-03 (`fct_sales`). Then P3-03, then P3-04 (reconciliation, depends on both P3-03 and P3-02).

## Open questions
_None blocking._ The full-data ingestion question is resolved (tactical Parquet form above; the
architecture already fixed the "seeds for units / full dataset for reconciliation" split).

## Worklog (most recent first)
- **P3-02 done** (PR #12) — `bridge_order_sales_reason` (order × sales reason, ADR-0003), staging +
  mart + 4 schema tests; `dbt build` PASS=105, `dbt test --select source:*` PASS=40. Inner loop skipped.
- P3-01 done (PR #11) — canonical AdventureWorks → DuckDB Parquet; 2011 gross reconciles exactly.
- **Phase 2 (Dimensions) complete** — 7/7 dims, PRs #4–#10, `dbt build` PASS=113 on develop @ `dec231d`.
- Phase 1 (Foundation) complete — P1-01..03, sources + seeds + source tests green.
