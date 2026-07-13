# PROGRESS — AdventureWorks Analytics Engineering

> **Durable loop state. Lives in the repo (never temp).** The single dynamic file — update it per
> completed slice. Static conventions/decisions go in the sources of truth, not here.
> Priming read order: `.sdd/profile.md` → **this file** → latest handoff (below) →
> `PRD.md` / `ARCHITECTURE.md` as needed.

## SDD-CURSOR
- **Phase:** 3 (Fact + reconciliation)
- **Doing:** — (P3-01, P3-02, P3-05, P3-03 all done; P3-04 not yet dispatched)
- **Next:** dispatch P3-04 (2011 reconciliation + fact/bridge invariants) — now unblocked
  (P3-03 + P3-02 both done). Last issue in Phase 3.
- **Stop-reason:** clean boundary — P3-03 landed green (PR #16); no blocker.

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

**P3-05 done** (PR #13): `dim_customer` reworked to one row per source customer (individual,
person-backed + store, reseller) with a new `customer_type` attribute; `dim_credit_card` gained a
synthetic "N/A" member for card-less reseller lines. P3-01's load script was extended to acquire the
`store` table (Store.csv, was missing from P3-01's in-scope list) — `stg_adventure_works__store` added,
`store` source declared. `dbt build` PASS=106 on the full local dataset (re-verified from a clean clone);
2011 gross reconciliation still holds exactly after re-running `just load`. Both Phase-3 dim FKs
(`customer_key`, `credit_card_key`) now resolve for reseller lines — **P3-03 unblocked**.

**P3-03 done** (PR #16): `fct_sales` built at order-line grain over **all channels**. New
`stg_adventure_works__salesorderdetail` staging view (was missing); fixed a stale online-only filter in
`stg_adventure_works__salesorderheader` that predated ADR-0010 (would have silently dropped reseller
lines from the whole downstream lineage) — `online_order_flag` now carries through as `is_online`. New
`int_sales__order_lines` (ephemeral) joins detail + header + ship-to address/state/country and resolves
all 7 dim surrogate keys via the same `generate_surrogate_key` inputs each dim hashes on. `fct_sales`:
`sales_fact_key` PK, 7 FKs, degenerate `sales_order_number`/`sales_order_line_number`/`is_online`,
`gross_revenue`/`discount_amount`/`net_revenue` (ADR-0001/0004/0005/0007/0010). Outer BDD: 21 dbt schema
tests (PK unique+not_null, relationships to all 7 dims, not_null on FKs+measures) authored and committed
RED (dbt warned "Did not find matching node for patch with name 'fct_sales'" — 0 of 21 ran) before the
model existed, then green (21/21) once it landed. `dbt build` PASS=135 (clean re-run: wiped
`target/`/`dbt_packages/`/the DuckDB file, `dbt deps` + `dbt build` from scratch); `dbt test --select
source:*` PASS=44. Verified independently: 121,317 fact rows = source `salesorderdetail` row count
exactly; `is_online` splits 60,398 online / 60,919 reseller; `net_revenue` sums to source `LineTotal`
exactly (diff 0.0000); 2011 `gross_revenue` = 12,646,112.16 exactly — **de-risks P3-04's reconciliation
test.** Inner loop was `skipped` per the issue.

**Next:** dispatch P3-04 (2011 reconciliation + fact/bridge invariants) — last issue in Phase 3.

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
- **P3-01's in-scope table list missed `store`** (needed by P3-05 for reseller customer names). P3-05
  extended `scripts/load_adventure_works.py` to acquire it (`Store.csv`, `+|`/`&|` delimited like
  `Person.csv`) rather than escalating — a tactical, reversible completion of an existing acquisition
  step, not a new architectural decision.

## In review (PR open, awaiting merge) — n/a under auto-merge
_Empty: auto-merge lands issues straight to `done`._

## Latest handoff
_none — Phase 2 closed at a clean boundary; files describe the position._

## Next actions
1. Phase-3 backlog **approved** (confirm gate passed).
2. P3-01, P3-02, P3-05, P3-03 all done. **Dispatch P3-04** (2011 reconciliation + fact/bridge
   invariants) — now unblocked (depends on both P3-03 and P3-02). Last issue in Phase 3.

## Open questions
_None blocking._ The full-data ingestion question is resolved (tactical Parquet form above; the
architecture already fixed the "seeds for units / full dataset for reconciliation" split).

## Worklog (most recent first)
- **P3-03 done** (PR #16): `fct_sales` at order-line grain, all channels — 7 FKs, `is_online`,
  gross/discount/net measures; fixed stale online-only staging filter (ADR-0010); 21 outer schema
  tests RED-then-green; `dbt build` PASS=135; net_revenue and 2011 gross both reconcile exactly.
- **P3-05 done** (PR #13): all-channel dim rework — `dim_customer` (+store customers,
  `customer_type`) and `dim_credit_card` (+"N/A" member); extended P3-01's load script + source
  for the `store` table. `dbt build` PASS=106; clean re-run verified. Unblocks P3-03.
- **P3-02 done** (PR #12) — `bridge_order_sales_reason` (order × sales reason, ADR-0003), staging +
  mart + 4 schema tests; `dbt build` PASS=105, `dbt test --select source:*` PASS=40. Inner loop skipped.
- P3-01 done + verified (PR #11) — canonical AdventureWorks → DuckDB Parquet, 2011 gross reconciles
  exactly = $12,646,112.16 (all-sales); scope amended to all channels (ADR-0010).
- **Phase 2 (Dimensions) complete** — 7/7 dims, PRs #4–#10, `dbt build` PASS=113 on develop @ `dec231d`.
- Phase 1 (Foundation) complete — P1-01..03, sources + seeds + source tests green.
