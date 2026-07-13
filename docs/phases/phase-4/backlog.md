# Phase 4 — Serving · Backlog

> Parent: [`docs/phases/phase-4/prd.md`](prd.md). Integration branch `develop`; each issue on
> `issue/<id>-<slug>`, auto-merge via gh PR. Statuses: `todo → doing → done`.
> Test command: `just build` (non-regression only — Phase 4 adds no dbt models) plus this phase's own
> checks (Superset dataset/chart import + reconciliation query, notebook end-to-end run). BI tool =
> Apache Superset, BI-as-code (ADR-0002). No new dbt seam exists for this phase — every chart/KPI reads
> the already-tested `fct_sales` / `dim_*` / `bridge_order_sales_reason` marts (Phase 2–3, NFR-3, "no
> parallel metric layer"); each scenario's `Then` is a reconciliation check against those same marts.
> Each slice is vertical: Superset dataset registration → chart(s) → dashboard placement → YAML export
> committed under `bi/`, demoable end-to-end.

| ID | Title | Status | Blocked by |
|----|-------|--------|-----------|
| P4-01 | Superset ↔ DuckDB scaffold + hero KPI tiles (Revenue, Orders, Units, AOV) | done | — |
| P4-02 | Question a — orders/qty/value sliced + filtered by all required dims | todo | P4-01 |
| P4-03 | Question b — top products by AOV by month/year/geography | todo | P4-01 |
| P4-04 | Question c — top-10 customers by revenue | todo | P4-01 |
| P4-05 | Question d — top-5 cities by revenue | todo | P4-01 |
| P4-06 | Question e — orders/qty/value time series by month & year | doing | P4-01 |
| P4-07 | Question f + Promotion-impact hero KPI | todo | P4-01 |
| P4-08 | Deliverable-equivalence packaging (dashboard assembly + run instructions) | todo | P4-01..P4-07 |
| P4-09 | EDA notebook | done | — |
| P4-10 | Commercial recommendations doc | todo | P4-08, P4-09 |

P4-01 registers the Superset↔DuckDB connection and datasets every later BI issue (P4-02–P4-08) depends
on. P4-02–P4-07 are mutually independent charts once P4-01 lands (each answers one `CHALLENGE.md`
business question) and may be built in any order among themselves. P4-08 assembles them into one
dashboard and finalizes the deliverable-equivalence bundle, so it waits on all of them. P4-09 (EDA
notebook) only needs the Phase 3 marts — independent of the Superset track, can start immediately.
P4-10 (recommendations) needs both the finished dashboard and the EDA insights to cite real numbers.

---

## P4-01 — Superset ↔ DuckDB scaffold + hero KPI tiles

### What to build
A BI-as-code Superset project under `bi/` connected via SQLAlchemy to the local DuckDB file holding the
built marts (read-only). Register datasets for `fct_sales` and the dims/bridge needed by the hero KPIs.
Build the three hero-KPI tiles from `FR-8`: **Total Sales Revenue**, **Number of Orders**, **Units
Sold**, and **Average Order Value** (`(gross − discount) ÷ distinct orders`, per `ARCHITECTURE.md`
§fct_sales). Export the database connection, datasets, charts as YAML and commit them — the foundation
every later BI issue (P4-02–P4-08) builds datasets/charts on top of.

### Acceptance criteria
```gherkin
Scenario: hero KPI tiles reconcile to the tested fct_sales aggregates
  Given the built fct_sales mart registered as a Superset dataset over the local DuckDB file
  When I import the exported bi/ YAML bundle into Superset and render the hero KPI tiles
  Then Total Sales Revenue equals sum(gross_revenue) computed directly from fct_sales
  And Number of Orders equals count(distinct sales_order_number) from fct_sales
  And Units Sold equals sum(order_qty) from fct_sales
  And Average Order Value equals (sum(gross_revenue) - sum(discount_amount)) / count(distinct sales_order_number)
```
- [ ] `bi/` Superset-as-code project scaffold (database connection YAML, pointed at the local DuckDB file)
- [ ] Datasets registered for `fct_sales` (+ any dims the KPI tiles need)
- [ ] Four hero-KPI charts (Total Revenue, Orders, Units Sold, AOV) exported as YAML
- [ ] A validation query/script proving each tile's number against a direct `fct_sales` aggregate
- [ ] Run instructions stub (how to point Superset at the local DuckDB file and import `bi/`)

### Inner loop (TDD)
`skipped — declarative chart/metric config wired to already-tested marts; the reconciliation check in
the scenario is the gate, there is no unit-decomposable branching logic in this slice`

### Blocked by
None — can start immediately (Phase 3 done).

---

## P4-02 — Question a: orders/quantity/value sliced and filtered

### What to build
`CHALLENGE.md` question a: "number of orders, quantity purchased, and total transaction value by
product, card type, sales reason, sales date, customer, status, city, state, and country." A chart (or
small set of charts) over `fct_sales` (joined to `dim_product`, `dim_credit_card`, `dim_order_status`,
`dim_geography`, `dim_date`, `dim_customer`, and `bridge_order_sales_reason` for the reason slice)
exposing orders/qty/value, sliceable by each of those dims. Wire the required dashboard filters
(`FR-7`): product, card type, sales reason, order date, customer, order status, city, state, country,
sales channel (`is_online`).

### Acceptance criteria
```gherkin
Scenario: question a is answerable sliced and filtered by every required dimension
  Given the Superset datasets registered in P4-01 over fct_sales and its seven dims plus the bridge
  When I apply a filter (e.g. product = a known SKU, sales channel = online) on the question-a chart
  Then the displayed order count, quantity, and total value match a direct aggregate query over fct_sales
    with the same filter applied
  And the chart can be re-sliced by each of product, card type, sales reason, sales date, customer,
    status, city, state, and country without error
```
- [ ] Chart(s) answering question a, sliceable across all nine required dimensions
- [ ] Dashboard filter set: product, card type, sales reason, order date, customer, order status, city,
      state, country, sales channel
- [ ] Chart/dataset YAML exported and committed

### Inner loop (TDD)
`skipped — declarative Superset chart/filter config over already-tested marts; the reconciliation check
against a direct fct_sales aggregate is the gate`

### Blocked by
P4-01 (dataset registration + connection scaffold).

---

## P4-03 — Question b: top products by AOV by month/year/geography

### What to build
`CHALLENGE.md` question b: "which products have the highest average order value by month, year, city,
state, and country?" A chart ranking products by AOV (`(gross − discount) ÷ distinct orders`, per
`ARCHITECTURE.md` §fct_sales), sliceable/filterable by month, year, city, state, country.

### Acceptance criteria
```gherkin
Scenario: top products by AOV reconciles to a direct fct_sales computation
  Given the Superset datasets registered in P4-01
  When I render the question-b chart filtered to a specific year and state
  Then the top-ranked product's AOV equals (sum(gross_revenue) - sum(discount_amount)) / count(distinct
    sales_order_number) computed directly over fct_sales for that product, year, and state
```
- [ ] Chart ranking products by AOV, filterable by month, year, city, state, country
- [ ] Chart/dataset YAML exported and committed

### Inner loop (TDD)
`skipped — declarative chart config over already-tested marts; direct-aggregate reconciliation is the
gate`

### Blocked by
P4-01.

---

## P4-04 — Question c: top-10 customers by revenue

### What to build
`CHALLENGE.md` question c: "top 10 customers by total transaction value, filtered by product, card
type, sales reason, sales date, status, city, state, and country." A chart ranking `dim_customer` by
`sum(gross_revenue)` (or `net_revenue` — decide and document per `FR-6`/`ARCHITECTURE.md` metric
definitions), limited to top 10, with the listed filters wired.

### Acceptance criteria
```gherkin
Scenario: top-10 customers reconciles to a direct fct_sales aggregate
  Given the Superset datasets registered in P4-01
  When I render the question-c chart with no filters applied
  Then it lists exactly 10 customers ranked by total transaction value
  And the top customer's value equals the corresponding direct aggregate over fct_sales joined to
    dim_customer
```
- [ ] Top-10-customers chart (ranked, limited to 10) with the required filter set wired
- [ ] Chart/dataset YAML exported and committed

### Inner loop (TDD)
`skipped — declarative ranked/limited chart over already-tested marts; direct-aggregate reconciliation
is the gate`

### Blocked by
P4-01.

---

## P4-05 — Question d: top-5 cities by revenue

### What to build
`CHALLENGE.md` question d: "top 5 cities by total transaction value, filtered by product, card type,
sales reason, sales date, customer, status, city, state, and country." A chart ranking `dim_geography`
cities by total transaction value, limited to top 5, with the listed filters wired.

### Acceptance criteria
```gherkin
Scenario: top-5 cities reconciles to a direct fct_sales aggregate
  Given the Superset datasets registered in P4-01
  When I render the question-d chart with no filters applied
  Then it lists exactly 5 cities ranked by total transaction value
  And the top city's value equals the corresponding direct aggregate over fct_sales joined to
    dim_geography (ship-to, ADR-0005)
```
- [ ] Top-5-cities chart (ranked, limited to 5) with the required filter set wired
- [ ] Chart/dataset YAML exported and committed

### Inner loop (TDD)
`skipped — declarative ranked/limited chart over already-tested marts; direct-aggregate reconciliation
is the gate`

### Blocked by
P4-01.

---

## P4-06 — Question e: time series by month & year

### What to build
`CHALLENGE.md` question e: "number of orders, quantity purchased, and total transaction value by month
and year" as a time-series chart (per the challenge's own hint), over `fct_sales` joined to `dim_date`.

### Acceptance criteria
```gherkin
Scenario: monthly/yearly time series reconciles to a direct fct_sales aggregate
  Given the Superset datasets registered in P4-01, including dim_date
  When I render the question-e time-series chart grouped by year-month
  Then each point's order count, quantity, and total value equal the corresponding direct aggregate
    over fct_sales joined to dim_date for that year-month
  And the series covers the full order date range with no gaps (dim_date is gap-free, ADR-0006)
```
- [ ] Time-series chart (month & year grain) for orders, quantity, and value
- [ ] Chart/dataset YAML exported and committed

### Inner loop (TDD)
`skipped — declarative time-series chart over already-tested marts; direct-aggregate reconciliation is
the gate`

### Blocked by
P4-01.

---

## P4-07 — Question f + Promotion-impact hero KPI

### What to build
`CHALLENGE.md` question f: "which product has the highest number of units purchased for the
'Promotion' sales reason?" Joins `fct_sales → sales_order_number → bridge_order_sales_reason →
dim_sales_reason` filtered to `sales_reason_name = 'Promotion'` (`ADR-0003` — the base fact carries no
reason FK, so this join does not fan out gross for a single-reason filter, per the invariant `P3-04`
already tests). Also builds the third hero KPI (`FR-8`): **Promotion-impact** — a discount/promotion
impact figure (e.g. total `discount_amount` for Promotion-reason orders, or discount as a % of gross)
presented alongside the P4-01 hero tiles.

### Acceptance criteria
```gherkin
Scenario: the Promotion-reason top product and impact KPI reconcile to a direct bridge join
  Given the built fct_sales and bridge_order_sales_reason marts registered in Superset
  When I render the question-f chart filtered to sales_reason_name = "Promotion"
  Then the top-ranked product's unit count equals sum(order_qty) computed directly by joining
    fct_sales to bridge_order_sales_reason filtered to "Promotion" and grouping by product
  And the Promotion-impact hero KPI equals the corresponding direct aggregate over the same join
```
- [ ] Question-f chart (top product by units, Promotion reason filter)
- [ ] Promotion-impact hero KPI tile, placed alongside the P4-01 hero tiles
- [ ] Chart/dataset YAML exported and committed

### Inner loop (TDD)
`skipped — declarative chart over already-tested marts; the bridge-join reconciliation check is the
gate, and the no-fan-out invariant is already proven by P3-04's singular test`

### Blocked by
P4-01.

---

## P4-08 — Deliverable-equivalence packaging

### What to build
Assemble every chart from P4-01–P4-07 onto one committed Superset dashboard (BI-as-code), with the
global sales-channel filter (`is_online`, online/reseller) applied dashboard-wide alongside the other
required filters (`FR-7`). Finalize the deliverable-equivalence bundle (`FR-9`, `ADR-0002`): the full
dashboard/dataset **YAML/JSON bundle** committed under `bi/`, **run instructions** (how a grader
re-imports/re-runs the dashboard locally against the built DuckDB file), and **documented metric
definitions** (the analogue of documented DAX — one definition per KPI/measure used across the
dashboard, referencing the `fct_sales`/`ARCHITECTURE.md` metric formulas).

### Acceptance criteria
```gherkin
Scenario: the full dashboard bundle is importable and answers every business question with the required filters
  Given the committed bi/ YAML bundle (datasets, charts, dashboard from P4-01–P4-07)
  When a grader follows the committed run instructions to import the bundle into a local Superset
    pointed at the built DuckDB file
  Then all six business-question charts (a-f) and all four hero KPI tiles render without error
  And the sales-channel filter (online/reseller) and the other required filters apply dashboard-wide
  And every KPI/measure used has a documented definition committed alongside the bundle
```
- [ ] One dashboard assembling all P4-01–P4-07 charts + hero KPIs
- [ ] Dashboard-wide sales-channel filter + the other `FR-7` filters
- [ ] Run instructions (local import/re-run against the built DuckDB file)
- [ ] Documented metric definitions for every KPI/measure on the dashboard
- [ ] Full bundle re-verified importable from a clean checkout

### Inner loop (TDD)
`skipped — packaging/assembly and documentation, no unit-decomposable logic; the import-and-render
scenario is the gate`

### Blocked by
P4-01, P4-02, P4-03, P4-04, P4-05, P4-06, P4-07.

---

## P4-09 — EDA notebook

### What to build
An exploratory data analysis notebook under `notebooks/` (`FR-11`), reading the same built DuckDB marts
(no separate extract, per `CLAUDE.md`'s "Python is a thin layer" convention) — code, charts, and
commentary per insight, covering at minimum: product mix, customer/channel distribution
(online vs. reseller, `is_online`), geography distribution, and the "Promotion" discount impact
(feeding P4-10's recommendations and cross-checking P4-01/P4-07's hero KPIs from an independent angle).

### Acceptance criteria
```gherkin
Scenario: the EDA notebook runs end-to-end over the built marts and documents its insights
  Given the built dim_* and fct_sales marts in the local DuckDB file
  When I execute notebooks/eda.ipynb top-to-bottom with no manual intervention
  Then it completes with no errors
  And it contains at least one chart and one commentary cell for each of: product mix, channel
    distribution, geography distribution, and promotion/discount impact
```
- [ ] `notebooks/eda.ipynb` (or `.py`) reading the built DuckDB marts directly
- [ ] Charts + per-insight commentary for the required topics
- [ ] Runs clean end-to-end from a fresh `uv run` environment

### Inner loop (TDD)
`skipped — exploratory/narrative notebook work, no unit-decomposable logic to isolate; the end-to-end
run + required-sections check in the scenario is the real gate`

### Blocked by
None — can start immediately (only needs Phase 3 marts; independent of the Superset track).

---

## P4-10 — Commercial recommendations doc

### What to build
An actionable, prioritized commercial recommendations document (`FR-10`) for Adventure Works, explicitly
framed for Silvana Teixeira (the skeptical Commercial Director persona in `PRD.md`) — each recommendation
grounded in a specific number pulled from the finished dashboard (P4-08) and/or the EDA notebook (P4-09),
not a generic statement.

### Acceptance criteria
```gherkin
Scenario: recommendations are actionable and each cites a specific reconciled figure
  Given the finished dashboard (P4-08) and EDA notebook (P4-09)
  When I review the recommendations document
  Then it contains a prioritized list of concrete, actionable recommendations
  And each recommendation cites at least one specific number drawn from the dashboard or EDA output
  And at least one recommendation directly addresses Silvana's stated skepticism (promotions vs.
    data-driven decisions) using the question-f / Promotion-impact figures
```
- [ ] Recommendations document (markdown or PDF), prioritized, each item citing a concrete figure
- [ ] At least one recommendation explicitly ties to the Promotion-vs-data-driven skepticism (question f)

### Inner loop (TDD)
`skipped — narrative writing, no unit-decomposable logic; the citation-check scenario is the gate`

### Blocked by
P4-08, P4-09.
