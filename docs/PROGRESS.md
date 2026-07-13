# PROGRESS — AdventureWorks Analytics Engineering

> **Durable loop state. Lives in the repo (never temp).** The single dynamic file — update it per
> completed slice. Static conventions/decisions go in the sources of truth, not here.
> Priming read order: `.sdd/profile.md` → **this file** → latest handoff (below) →
> `PRD.md` / `ARCHITECTURE.md` as needed.

## SDD-CURSOR
- **Phase:** 4 (Serving)
- **Doing:** none
- **Next:** P4-02, P4-03, P4-05, P4-06, P4-07 (remaining business questions, any order, unblocked by
  P4-01); P4-08 waits on P4-02..P4-07; P4-10 waits on P4-08 + P4-09 (**P4-09 done**).
- **Stop-reason:** none — P4-01, P4-04, and P4-09 all landed green; P4-02, P4-03, P4-05, P4-06, P4-07
  are the next unblocked slices.

## Current status
**Phase 3 (Fact + reconciliation) COMPLETE — 5/5 issues done** (P3-01 canonical AdventureWorks →
DuckDB Parquet; P3-02 `bridge_order_sales_reason`; P3-05 all-channel dim rework — **ADR-0010** amended
scope to all sales channels, not online-only; P3-03 `fct_sales` at order-line grain, all channels, 7
FKs; P3-04 the régua-headline reconciliation tests). All phase DoD gates green: `dbt build` PASS=138,
`dbt test --select source:*` PASS=44, all PK/FK/data-quality/reconciliation tests pass, **2011 all-
channel gross reconciles exactly to $12,646,112.16**, `net_revenue` sums to source `LineTotal` exactly,
fact/bridge fully documented. Per-issue detail lives in the Worklog below and each PR (#11–#18); a
post-merge fix (PR #22, see Tactical decisions) later corrected a vacuous-pass literal in P3-04's bridge
invariant test.

**Phase 4 (Serving) opened and IN PROGRESS.** `docs/phases/phase-4/prd.md` + `backlog.md` (10 issues,
realizing FR-6/7/8/9/10/11 + NFR-3) committed and confirmed.

**P4-01 done**: BI-as-code Superset scaffold under `bi/` (ADR-0002) — SQLAlchemy database connection
to the local DuckDB file (`bi/databases/adventureworks_duckdb.yaml`), a `fct_sales` dataset
(`bi/datasets/main/fct_sales.yaml`) with four declared hero-KPI metrics (`total_sales_revenue`,
`number_of_orders`, `units_sold`, `average_order_value` — FR-8, formulas exactly match
`ARCHITECTURE.md` §fct_sales, no parallel metric layer per NFR-3), and four `big_number_total` hero
charts exported as YAML under `bi/charts/`. Outer BDD test: `scripts/validate_hero_kpis.py` reads
each hero chart's declared metric SQL straight from the committed YAML and asserts it equals a
direct `fct_sales` aggregate written independently — RED proven (`FileNotFoundError` on
`bi/datasets/main/fct_sales.yaml`, committed alone) before `bi/` existed, GREEN once the scaffold
landed (all four reconcile exactly: revenue 110,373,889.3134; orders 31,465; units 274,914; AOV
3,491.065672966407). `bi/README.md` has the run instructions (local Superset import) + a documented
metric-definitions table (`FR-9`). Inner loop `skipped` per the issue (declarative config, no
unit-decomposable logic). No dbt models changed — `just build` clean-checkout stays PASS=138
(non-regression; Phase 4 adds no dbt models). Superset itself is not installed in this environment
(BI-as-code — the runtime is separate from the repo's Python deps), so import was not exercised
against a live server; reconciliation was proven directly against the built DuckDB file instead, per
the issue's own scope note. **Unblocks P4-02..P4-08.**

**P4-09 done** (PR #20): `notebooks/eda.ipynb` — an EDA notebook reading `data/adventureworks.duckdb`'s
built marts directly via a DuckDB connection (no separate extract, per `CLAUDE.md`'s "Python is a thin
layer" convention), with a chart + grounded commentary for each of the four required topics: product
mix, channel distribution (`is_online`), geography distribution, and Promotion/discount impact. Outer
BDD: `scripts/check_eda_notebook.py` (`just eda`) executes the notebook end-to-end via `nbclient` and
asserts no cell errors plus all four required chart+commentary sections present. RED proven
(`notebooks/eda.ipynb` did not exist), committed alone; while building the notebook found and fixed a
check-script bug (markdown heading matching wasn't restricted to actual `#` headings, so the intro
paragraph's own prose could satisfy a section before any chart cell was reached) — committed as a
separate, strictly-stronger test-only fix before the implementation commit. GREEN once
`notebooks/eda.ipynb` landed; re-verified from a fully clean state (wiped `.venv`, `target/`,
`dbt_packages/`, the DuckDB file, re-ran `just setup && just build && just eda`). `just build`
non-regression: PASS=138 (Phase 4 adds no dbt models). `just check` (lint+typecheck+build) green.

Grounded numbers (reconcile to the tested marts, independent of Superset's chart engine): product mix
— Bikes ~86% of gross revenue from ~30% of units; channel — resellers are ~12% of orders but ~73% of
revenue (AOV ~$21.3K vs ~$1.06K online, ~20x gap); geography — the US alone is ~57% of gross revenue;
promotion — 3,515 online "On Promotion" orders = $6,361,828.95 gross, confirmed identical via direct
`fct_sales` sum and the bridge join (no fan-out, same invariant P3-04's singular test proves
structurally). **Flags a nuance for P4-07/P4-10**: P3-04's singular test filters the literal string
`sales_reason_name = 'Promotion'`, which matches **no row** in `dim_sales_reason` — the actual reason is
named `"On Promotion"` with `sales_reason_type = 'Promotion'`. The test still passes today because both
sides of its comparison are vacuously `NULL` (no matched orders), not because the invariant was actually
exercised on a non-empty set. P4-07 (question f) uses the same literal-string filter in its Gherkin —
that scenario will need `sales_reason_type = 'Promotion'` (or `sales_reason_name = 'On Promotion'`) to
return real data; flagging here rather than silently fixing P3-04 (closed, not this issue's scope). Also
found: the notebook's real `discount_amount` ($527,507.91 total) sits entirely on the reseller/store
channel (60,919 lines), zero on the 60,398 online lines — the online "Promotion" reason tag and the
fact's dollar discount are two structurally distinct phenomena on opposite channels, a nuance worth
surfacing to P4-10's recommendations. Inner loop `skipped` per the issue (exploratory/narrative
notebook, no unit-decomposable logic). **Independent of the Superset track — does not unblock/depend on
P4-01..P4-08.**

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
- **Fixed P3-04's vacuous-pass bug** (PR #22, `fix/P3-04-promotion-reason-literal`): the merged
  `fct_sales_gross_invariant_under_bridge` test filtered `sales_reason_name = 'Promotion'`, matching
  zero rows (real value `'On Promotion'`) — it had been passing on both sides `NULL` since P3-04
  landed, never exercising the no-fan-out invariant. Found by P4-09's EDA cross-check. Corrected the
  literal (3,515 matched orders, gross reconciles exactly non-vacuously) and added a zero-match guard
  so a future rename can't silently pass again — strictly strengthens the assertion. Landed outside the
  normal issue flow (orchestrator-authored fix, not a backlog issue) since it corrects an existing
  merged test rather than building new scope; the merge itself required explicit user authorization
  (the standing `auto-merge` policy covers issue-worker dispatches, not orchestrator self-merges).

## In review (PR open, awaiting merge) — n/a under auto-merge
_Empty: auto-merge lands issues straight to `done`._

## Latest handoff
_none — Phase 2 closed at a clean boundary; files describe the position._

## Next actions
1. Phase-3 backlog **approved and fully drained** (5/5 issues done, P3-04 last).
2. **Phase 4 (Serving) opened and confirmed** — `docs/phases/phase-4/prd.md` (realizes
   FR-6/7/8/9/10/11, NFR-3) + `docs/phases/phase-4/backlog.md` (10 issues).
3. **P4-01 done** — Superset scaffold + hero KPI tiles landed; datasets/connection ready for
   P4-02..P4-08 to build on. P4-02..P4-07 (business questions a–f) can now proceed in any order.
4. **P4-09 done** — EDA notebook landed (independent of the Superset track). Flags a P3-04
   literal-string filter nuance (`sales_reason_name = 'Promotion'` matches no row; use
   `sales_reason_type = 'Promotion'` / `sales_reason_name = 'On Promotion'`) relevant to **P4-07**'s
   scenario before that issue is picked up.
5. **P4-04 done** — top-10-customers (question c) chart landed. Remaining: P4-02, P4-03, P4-05,
   P4-06, P4-07 → P4-08 → P4-10.

## Open questions
_None blocking._ The full-data ingestion question is resolved (tactical Parquet form above; the
architecture already fixed the "seeds for units / full dataset for reconciliation" split).
**Resolved:** P3-04's vacuous-pass literal-string bug (`sales_reason_name = 'Promotion'` → 0 rows) is
fixed on `develop` (PR #22, see Tactical decisions) — the test now matches the real `'On Promotion'`
value non-vacuously. **P4-07's worker should use `sales_reason_name = 'On Promotion'`** (or
`sales_reason_type = 'Promotion'`) in its own scenario realization — same literal now proven correct
against real data (3,515 matched orders), no rediscovery needed.

## Worklog (most recent first)
- **P4-04 done**: `bi/datasets/main/question_c_top10_customers.yaml` (virtual dataset joining
  `fct_sales` to `dim_customer` and the six other required-filter dims, with a scalar per-order
  sales-reason subquery over `bridge_order_sales_reason` — no join fan-out) + a `table` chart
  (`bi/charts/question_c_top10_customers.yaml`) ranking customers by `total_transaction_value`
  (`row_limit: 10`, `order_desc: true`). **Documented metric choice**: total transaction value =
  **gross revenue** (`SUM(gross_revenue)`), matching the P4-01 hero KPI "Total Sales Revenue" and
  the régua's headline gross figure — no parallel net-revenue ranking introduced (documented in
  `bi/README.md`'s new "business questions" metric table and in the dataset YAML's metric
  description). Outer test `scripts/test_top10_customers.py` RED (`bi/datasets/main/
  question_c_top10_customers.yaml` absent) → committed alone → GREEN once the dataset/chart landed
  (top customer "Brakes and Gears" = $882,276.4966, exact match against a direct
  `fct_sales`/`dim_customer` aggregate). `just build` non-regression PASS=138; `just check` green;
  re-verified from a fully clean state (wiped `.venv`, `dbt_packages`, the DuckDB file, re-ran
  `uv sync && dbt deps && just build`). Inner loop skipped per issue.
- **P4-09 done** (PR #20): `notebooks/eda.ipynb` — chart + commentary for product mix, channel
  distribution (`is_online`), geography distribution, Promotion/discount impact, reading the built
  marts directly via DuckDB. Outer test `scripts/check_eda_notebook.py` (`just eda`) RED (notebook
  absent) → committed alone; found + fixed a heading-matching bug in the checker (stronger, separate
  commit) → GREEN once the notebook landed, re-verified from a fully clean state. `just build`
  non-regression PASS=138; `just check` green. Flags a P3-04 literal-string nuance relevant to P4-07.
  Inner loop skipped per issue. Independent of the Superset track.
- **P4-01 done**: `bi/` Superset-as-code scaffold (ADR-0002) — database connection to the local
  DuckDB file, `fct_sales` dataset with 4 declared hero-KPI metrics (Total Revenue, Orders, Units
  Sold, AOV — FR-8), 4 `big_number_total` hero charts. Outer test `scripts/validate_hero_kpis.py`
  RED (bi/ absent) → committed alone → GREEN (all 4 KPIs reconcile exactly to direct `fct_sales`
  aggregates). `just build` non-regression PASS=138. Inner loop skipped per issue. Unblocks
  P4-02..P4-08.
- **Phase 3 (Fact + reconciliation) COMPLETE — 5/5 issues** (PRs #11–#18): P3-01 canonical
  AdventureWorks → DuckDB Parquet (2011 gross = $12,646,112.16 exact); P3-02 `bridge_order_sales_reason`;
  P3-05 all-channel dim rework (ADR-0010); P3-03 `fct_sales` (order-line grain, 7 FKs, all channels);
  P3-04 the 3 régua-headline reconciliation/invariant tests. Final `dbt build` PASS=138.
- **Phase 2 (Dimensions) complete** — 7/7 dims, PRs #4–#10, `dbt build` PASS=113 on develop @ `dec231d`.
- Phase 1 (Foundation) complete — P1-01..03, sources + seeds + source tests green.
