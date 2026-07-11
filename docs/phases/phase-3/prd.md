# Phase 3 — Fact + Reconciliation

> **Derived layer** (assistant's phase projection — not separately grilled). Projects the validated
> baselines: root [`PRD.md`](../../PRD.md) by requirement ID, [`ARCHITECTURE.md`](../../ARCHITECTURE.md)
> by seam. Does **not** restate Problem/Solution. Phase-cutting rule: profile §Phase-cutting step 3 (Fact).

## Requirements realized
- **FR-2** — `fct_sales` at order-line grain over online orders, joinable to all seven dims, exposing
  order count, quantity, gross revenue, discount, net revenue.
- **FR-3** — Gross = `UnitPrice × OrderQty` (ADR-0001); **2011 gross reconciles to $12,646,112.16 exactly**
  via a singular test — the régua headline.
- **FR-4** *(completes for the fact/bridge)* — PK tests on `fct_sales`; fact→dim `relationships`;
  data-quality (not_null on measures/FKs, bridge unique-combo).
- **FR-5** *(fact/bridge scope)* — document every `fct_sales` / `bridge_order_sales_reason` column.

Lights up business questions **a, b, c, d, e** (the fact + dims) and **f** (bridge → Promotion). Answering
them in the dashboard is Phase 4; here the model must *support* them.

## Seams touched (ARCHITECTURE §Seams)
1. **dbt sources** — repoint the `adventure_works` source to the full committed Parquet
   (`external_location`); source tests now run on real data. *(Bronze boundary.)*
2. **Model schema / PK tests** — `fct_sales` + `bridge_order_sales_reason`: `unique`+`not_null` PK,
   fact→dim `relationships`, not_null on FKs/measures, bridge `unique_combination_of_columns`. *(Gold.)*
3. **Singular reconciliation tests** — 2011 gross = $12,646,112.16 exact; `net_revenue = Σ LineTotal`;
   gross-invariant-under-bridge-join; order-line grain uniqueness. *(Reconciliation seam.)*

## Phase DoD gate (profile §DoD, this phase's scope)
- `dbt build` green offline against the **full local dataset** (models + all tests).
- `dbt test --select source:*` green on real data.
- `fct_sales` + bridge PK tests (`unique`+`not_null`) pass; fact→dim relationships pass.
- Data-quality tests (not_null FKs/measures, bridge unique-combo) pass.
- **2011 gross reconciliation test green — $12,646,112.16 exact.**
- `fct_sales` + bridge tables and columns documented.
- Verifier agent clears the branch/PR diff for test-gaming (profile integrity = prose+git+verifier).

## Dependencies
- **Phase 2 (Dimensions)** — done; all 7 dim surrogate keys exist for the fact FKs.
- **Full-data landing** — P3-01 acquires the canonical public AdventureWorks (DuckDB-only, no Postgres)
  into committed `data/adventure_works/*.parquet`. Fully autonomous. Reconciliation (P3-04) builds on it.

## Deferred to later phases
- **Phase 4 (Serving)** — EDA notebook, KPIs, Superset dashboard answering a–f (FR-6/7/8/9), commercial
  recommendations (FR-10), and the manual/external artifacts (FR-11–15).
