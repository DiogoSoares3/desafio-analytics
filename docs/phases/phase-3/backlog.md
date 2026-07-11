# Phase 3 — Fact + Reconciliation · Backlog

> Parent: [`docs/phases/phase-3/prd.md`](prd.md). Integration branch `develop`; each issue on
> `issue/<id>-<slug>`, auto-merge via gh PR. Statuses: `todo → doing → done`.
> Test command: `just build` · `just test-source` · `just lint`. Grain = order line (ADR-0004);
> gross = `UnitPrice × OrderQty` (ADR-0001); geography = ship-to (ADR-0005); reason via bridge (ADR-0003).
> Each slice is vertical: source/staging → int → `fct_*`/`bridge_*` mart → schema + singular tests + docs.

| ID | Title | Status | Blocked by |
|----|-------|--------|-----------|
| P3-01 | Acquire canonical AdventureWorks → DuckDB Parquet + repoint source | **done (PR #11)** | — |
| P3-02 | `bridge_order_sales_reason` (order × reason) | todo | P3-01 |
| P3-05 | All-channel dim rework: `dim_customer` (+stores) & `dim_credit_card` (+N/A) | todo | P3-01 |
| P3-03 | `fct_sales` (order-line grain, all channels, 7 FKs, metrics) | todo | P3-01, P3-05 |
| P3-04 | 2011 reconciliation + fact/bridge invariants | todo | P3-03, P3-02 |

P3-01 (done) gated the phase. **P3-05 reworks two done Phase-2 dims for all-channel scope (ADR-0010) and
must land before P3-03**, whose fact FKs (`customer_key`, `credit_card_key`) resolve over reseller lines.
P3-02 is independent. P3-04 asserts the audited numbers over the fact + bridge.

> **DuckDB-only — no Postgres.** The challenge data is the *canonical public Microsoft AdventureWorks*
> (the ERD is the stock AW 2008 OLTP schema; `$12,646,112.16` is the well-known AW figure). It is a
> public download, loaded straight into DuckDB — no live database, no Postgres scaffold.
>
> **Scope = ALL channels (ADR-0010).** P3-01 proved 2011 all-sales gross = `$12,646,112.16` (online-only
> = $3.86M, does not reconcile). `fct_sales` covers online + reseller; `is_online` is a filter attribute.

---

## P3-01 — Acquire canonical AdventureWorks → DuckDB Parquet

### What to build
A reproducible acquisition step (`scripts/load_adventure_works.py`, run via `just load`) that fetches the
public MS AdventureWorks OLTP data, loads the ~14 in-scope tables into DuckDB, and writes them to
committed `data/adventure_works/*.parquet` (the offline source-of-record — the grader gets them in the
clone). Repoint `_sources.yml` so each source table reads its Parquet via dbt-duckdb `external_location`
(`read_parquet('data/adventure_works/<t>.parquet')`). Add a `.gitignore` exception for
`data/adventure_works/*.parquet` (keep the DuckDB file ignored). Retire the 14 raw-table seed fixtures as
the source (Parquet replaces them); keep `order_status.csv` (a derived lookup, not an AW table).

### Acquisition intel (from supervisor probe — save the worker a blind rediscovery)
- Source: `github.com/microsoft/sql-server-samples` release `adventureworks` →
  `AdventureWorks-oltp-install-script.zip`. CSVs are **tab-delimited, NO header**; column order per the
  bundled `instawdb.sql` DDL. `SalesOrderDetail` = 11 cols (…OrderQty=4, ProductID=5, UnitPrice=7,
  UnitPriceDiscount=8, LineTotal=9); `SalesOrderHeader` = 26 cols (OrderDate=3, OnlineOrderFlag=7,
  SubTotal=20).
- ⚠️ **The current MS release date-shifts OrderDate to ~2022+ (classic-2011 + 11yr) — it has NO 2011 and
  will NOT reconcile.** Source a **fixed-date (2011–2014) AdventureWorks** instead (e.g. an AdventureWorks
  2017/2019 OLTP export, or a Postgres port such as `lorint/AdventureWorks-for-Postgres` that keeps 2011
  as the base year). **The reconciliation below is the oracle that proves you have the right dataset.**

### Acceptance criteria
```gherkin
Scenario: canonical AdventureWorks backs the source and reconciles to the audited 2011 figure
  Given the in-scope adventure_works tables loaded into data/adventure_works/*.parquet
  And _sources.yml points each table at its Parquet via read_parquet
  When I run "just test-source"
  Then every source test passes against the full dataset
  And salesorderheader reflects the full order set (not the seed fixture)
  And sum(UnitPrice * OrderQty) for orders dated 2011 equals 12646112.16 exactly
```
- [ ] `just load` / `scripts/load_adventure_works.py` — reproducible fetch + load → committed Parquet
- [ ] **Reconciliation proven in a scratch query: 2011 gross = 12646112.16 exact; report online-only vs
      all-sales** (settles the PRD scope question — flag the supervisor if online-only does NOT hold)
- [ ] `_sources.yml` `external_location` on all in-scope tables; `source()` unchanged downstream
- [ ] `.gitignore` exception for `data/adventure_works/*.parquet`; DuckDB file still ignored
- [ ] `just build` + `just test-source` green on the full data; the 7 dims still pass on real data

### Inner loop (TDD)
`required` — the 2011 reconciliation is the acceptance oracle; establish it (scratch query) before
committing the Parquet + wiring. This is the slice that de-risks the whole phase.

### Blocked by
None — first slice of the phase. Fully autonomous (public download; no AE action needed).

---

## P3-02 — bridge_order_sales_reason

### What to build
Staging view for `salesorderheadersalesreason`; an intermediate prep if needed; a
`bridge_order_sales_reason` mart at grain **order × sales reason** (ADR-0003), carrying
`sales_order_number` (degenerate order id) and the conformed `sales_reason_key` (join to
`dim_sales_reason`). No measures — the base fact carries no reason FK, so gross never fans out.

### Acceptance criteria
```gherkin
Scenario: bridge resolves orders to their sales reasons without fan-out
  Given staged salesorderheadersalesreason and dim_sales_reason
  When I run "just build"
  Then bridge_order_sales_reason has one row per order + sales reason
  And (sales_order_number, sales_reason_key) is unique
  And every sales_reason_key exists in dim_sales_reason
```
- [ ] `stg_adventure_works__salesorderheadersalesreason` (view)
- [ ] `bridge_order_sales_reason` mart; `sales_reason_key` via join to dim
- [ ] tests: `unique_combination_of_columns` on the grain; `relationships` to dim_sales_reason;
      not_null on both keys
- [ ] `_models.yml`: descriptions on model + every column

### Inner loop (TDD)
`skipped` — declarative bridge; unique-combo + relationships tests are the gate.

### Blocked by
P3-01 (needs full data + repointed source).

---

## P3-05 — All-channel dim rework (ADR-0010)

### What to build
Rework two done Phase-2 dims so the all-channel fact's FKs resolve for reseller lines.
- `dim_customer`: include **store customers** (`Customer.StoreID` not null) alongside individuals; add a
  `customer_type` attribute (`individual` / `store`). Staging for `store` if needed for the store name.
- `dim_credit_card`: add an explicit **"N/A" member** (surrogate for "no card") so reseller lines map to
  a real row and the fact FK stays `not_null`.

### Acceptance criteria
```gherkin
Scenario: dims cover all sales channels
  Given the full adventure_works customers (individual and store) and credit cards
  When I run "just build"
  Then dim_customer has one row per customer with customer_type in {individual, store}
  And dim_credit_card contains an "N/A" member for card-less (reseller) orders
  And both PKs stay unique + not_null and existing tests still pass
```
- [ ] `dim_customer` includes stores + `customer_type`; not_null full_name (store name for stores)
- [ ] `dim_credit_card` "N/A" member; `accepted_values` on card_type updated to include it
- [ ] `_models.yml` descriptions updated; existing dim tests still green

### Inner loop (TDD)
`skipped` — declarative dims; schema tests are the gate.

### Blocked by
P3-01. Must land **before** P3-03.

---

## P3-03 — fct_sales (order-line grain, all channels)

### What to build
Intermediate join assembling the order-line fact from staged `salesorderdetail` + `salesorderheader`
(**all channels** — no online filter, ADR-0010), resolving the seven dim surrogate keys (geography =
**ship-to**, ADR-0005; reseller lines → credit-card "N/A" member, store `customer_key`). A `fct_sales`
mart at one row per `salesorderdetailid` with: `sales_fact_key` (hash of salesorderdetailid), the 7 dim
FKs, degenerate `sales_order_number` + `sales_order_line_number` + **`is_online`** (channel filter),
`order_qty`, and measures `gross_revenue = UnitPrice × OrderQty`,
`discount_amount = UnitPriceDiscount × UnitPrice × OrderQty`, `net_revenue = gross − discount`.

### Acceptance criteria
```gherkin
Scenario: fct_sales is order-line grain over all channels and joins to every dimension
  Given staged salesorderdetail + salesorderheader (online + reseller) and the seven dims
  When I run "just build"
  Then fct_sales has one row per salesorderdetailid
  And sales_fact_key is unique and not null
  And is_online distinguishes online from reseller lines
  And every dim FK resolves (relationships to all seven dims pass, incl. reseller lines)
  And gross_revenue, discount_amount, net_revenue and order_qty are not null
```
- [ ] `int_sales__order_lines` (ephemeral) joining detail+header+dim lookups, **no channel filter**
- [ ] `fct_sales` mart: `sales_fact_key` surrogate; 7 FKs; degenerate dims incl. `is_online`; 3 measures + qty
- [ ] tests: PK `unique`+`not_null`; `relationships` to all 7 dims; not_null on FKs + measures
- [ ] `_models.yml`: descriptions on model + every column (metric definitions incl. ADR refs)

### Inner loop (TDD)
`skipped` — declarative SQL transform; schema/relationship tests are the gate. (Reconciliation logic
is exercised as a singular test in P3-04.)

### Blocked by
P3-01 (data) and P3-05 (all-channel dims). Independent of P3-02.

---

## P3-04 — 2011 reconciliation + fact/bridge invariants

### What to build
The régua headline: singular tests over the built fact/bridge. (1) 2011 gross sales =
**$12,646,112.16 exactly** (zero tolerance, ADR-0001). (2) `net_revenue` sums to source `LineTotal`.
(3) Gross is invariant under a single-reason bridge join (a "Promotion" filter does not fan out gross,
ADR-0003). (4) order-line grain uniqueness on `salesorderdetailid`.

### Acceptance criteria
```gherkin
Scenario: 2011 gross sales reconciles to the audited figure exactly
  Given fct_sales built over the full adventure_works sales (all channels)
  When I run "just build"
  Then sum of gross_revenue for orders dated in 2011 equals 12646112.16 exactly
  And net_revenue reconciles to the sum of source LineTotal
  And joining fct_sales to the sales-reason bridge does not inflate total gross_revenue
```
- [ ] `tests/fct_sales_gross_2011_reconciliation.sql` — fails unless 2011 gross = 12646112.16 exact
- [ ] `tests/fct_sales_net_revenue_reconciliation.sql` — net = Σ source LineTotal
- [ ] `tests/fct_sales_gross_invariant_under_bridge.sql` — bridge join preserves total gross
- [ ] grain uniqueness covered by P3-03 PK test (referenced, not duplicated)

### Inner loop (TDD)
`required` — the reconciliation is testable business logic; write the failing singular test first
(outer red), then make `fct_sales` produce the exact figure. This is the phase's trust anchor.

### Blocked by
P3-03 (fact) and P3-02 (bridge, for the invariant test).
