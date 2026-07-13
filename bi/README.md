# bi/ — Apache Superset BI-as-code (ADR-0002)

Committed export of the Superset assets (database connection, datasets, charts, and — from
`P4-08` on — the dashboard) that read the local DuckDB marts built by `just build`. No parallel
metric layer: every metric expression here is the same formula `ARCHITECTURE.md` §fct_sales
defines, and `scripts/validate_hero_kpis.py` proves it reconciles to a direct `fct_sales`
aggregate (NFR-3).

## Layout

```
bi/
  metadata.yaml                                     # Superset asset-bundle manifest
  databases/adventureworks_duckdb.yaml              # SQLAlchemy connection -> local DuckDB file
  datasets/main/fct_sales.yaml                      # fct_sales dataset + declared metrics
  datasets/main/question_a_sales_detail.yaml        # P4-02 -- fct_sales x 6 dims (product, card
                                                     #   type, status, geography, date, customer)
  datasets/main/question_a_sales_by_reason.yaml     # P4-02 -- fct_sales x bridge x dim_sales_reason
  datasets/main/question_b_product_aov.yaml         # P4-03 -- question-b virtual dataset
  datasets/main/question_c_top10_customers.yaml     # P4-04 -- question-c virtual dataset
  datasets/main/question_d_top_cities.yaml          # P4-05 -- question-d virtual dataset
  datasets/main/question_e_sales_by_month.yaml      # P4-06 -- question-e virtual dataset (fct_sales x dim_date)
  datasets/main/vw_promotion_reason_sales.yaml      # P4-07 -- virtual (SQL) dataset for question f
  charts/hero_*.yaml                                # the five hero-KPI tiles (big_number_total)
  charts/question_a_orders_qty_value.yaml           # P4-02 -- question a, sliced by product (+ 8 more)
  charts/question_a_orders_qty_value_by_reason.yaml # P4-02 -- question a's sales-reason slice
  charts/question_b_top_products_by_aov.yaml        # P4-03 -- question-b chart
  charts/question_c_top10_customers.yaml            # P4-04 -- top-10-customers table chart
  charts/question_d_top5_cities.yaml                # P4-05 -- top-5-cities table chart
  charts/question_e_orders_qty_value_by_month.yaml  # P4-06 -- question-e time-series chart
  charts/question_f_top_product_promotion.yaml      # P4-07 -- question f: top product, "On Promotion"
  dashboards/adventure_works_sales.yaml             # P4-08 -- the assembled dashboard bundle
```

## Dashboard — "Adventure Works — Sales" (`P4-08`)

`bi/dashboards/adventure_works_sales.yaml` is the deliverable-equivalence bundle (`FR-9`,
`ADR-0002`) assembling **every** chart from `P4-01`-`P4-07` onto one committed Superset dashboard:
the five hero-KPI tiles (Total Sales Revenue, Number of Orders, Units Sold, Average Order Value,
Promotion-Impact Revenue) and the seven charts answering `CHALLENGE.md` questions a-f (question a
has two charts -- detail + sales-reason slice, `P4-02`). Nothing built in the earlier issues is
left off.

A dashboard-wide native filter set realizes `FR-7`: **Sales Channel** (`is_online`,
online/reseller) plus **Product**, **Card Type**, **Sales Reason**, **Order Date**, **Customer**,
**Order Status**, **City**, **State/Province**, and **Country** -- each targets a real, declared
`filterable: true` column on `question_a_sales_detail` (the dataset carrying the full
required-filter column set, `P4-02`) or, for Sales Reason, `question_a_sales_by_reason` (kept
separate to avoid fanning out the other dims via the bridge join, `ADR-0003`). Native filters
apply dashboard-wide by default (Superset cross-filter scoping over `ROOT_ID`), so narrowing e.g.
sales channel = online reshapes every hero KPI and every question chart at once.

`scripts/test_dashboard_bundle.py` is the outer BDD test for the dashboard bundle (`P4-08`):
it reads the committed YAML directly (no live Superset needed, same pattern as the other
`validate_*`/`test_*` scripts) and asserts (1) every chart currently under `bi/charts/*.yaml` is
referenced in the dashboard's `position` tree, (2) every `FR-7` filter targets a real, filterable
column on a real, committed dataset, and (3) every metric used by any dataset the dashboard's
charts read is documented in this file's metric-definitions tables below.

```
uv run python scripts/test_dashboard_bundle.py
```

## Question a (P4-02) — orders/quantity/value sliced and filtered

`CHALLENGE.md` question a needs orders/quantity/value sliceable by product, card type, sales
reason, sales date, customer, status, city, state, country, and sales channel. Two virtual
Superset datasets realize this without fanning out the fact:

- `question_a_sales_detail.yaml` — `fct_sales` joined to its six single-valued dims (product,
  credit card, order status, geography [ship-to], date, customer). Every listed column is
  `filterable: true`, so the dashboard filter set (product, card type, order date, customer,
  order status, city, state, country, sales channel) applies directly. Chart:
  `question_a_orders_qty_value.yaml` (table, grouped by product by default; re-groupable by any
  other declared column).
- `question_a_sales_by_reason.yaml` — `fct_sales` joined through `bridge_order_sales_reason` to
  `dim_sales_reason` (ADR-0003). Kept as a **separate** dataset from the detail one so a
  multi-reason order does not fan out the other eight dims' totals; a single-reason
  filter/groupby on this dataset is exact (no fan-out — the same invariant P3-04's
  `fct_sales_gross_invariant_under_bridge` singular test proves structurally). Chart:
  `question_a_orders_qty_value_by_reason.yaml`.

Metrics on both datasets share the same formulas as the P4-01 hero KPIs: `number_of_orders =
COUNT(DISTINCT sales_order_number)`, `units_purchased = SUM(order_qty)`,
`total_transaction_value = SUM(gross_revenue)`.

`scripts/validate_question_a.py` is the outer BDD test: it reconciles a filtered aggregate
(product + sales channel) against a direct `fct_sales` join, then re-slices by all nine required
dimensions and checks each grouping's quantity/value totals sum back to the unfiltered grand
total (no fan-out) with no query errors:

```
uv run python scripts/validate_question_a.py
```

## Question c — top 10 customers by revenue (`P4-04`)

`CHALLENGE.md` question c: "top 10 customers by total transaction value, filtered by product, card
type, sales reason, sales date, status, city, state, and country." The
`question_c_top10_customers` dataset joins `fct_sales` to `dim_customer` and the other required
filter dims.

## Question d — top 5 cities by revenue (`P4-05`)

`CHALLENGE.md` question d: "top 5 cities by total transaction value, filtered by product, card
type, sales reason, sales date, customer, status, city, state, and country." The
`question_d_top_cities` dataset is a **virtual** (SQL-defined) Superset dataset joining `fct_sales`
to `dim_product`, `dim_credit_card`, `dim_order_status`, `dim_date`, `dim_customer`, and
`dim_geography` (ship-to, ADR-0005) — one row per sales-order line, no fan-out (ADR-0004). The
sales-reason filter column is resolved per line via a correlated subquery over
`bridge_order_sales_reason`/`dim_sales_reason` (ADR-0003) rather than a join, so grouping/aggregating
over this dataset never fans out the fact grain, even before any reason filter narrows it to a
single value. The `question_d_top5_cities` chart (`table`, `query_mode: aggregate`) groups by
`city`, ranks by `total_transaction_value` descending, and limits to 5 rows.

## Run instructions

### Option A — Docker Compose (recommended; no local Superset/Python install)
A single local container (Superset + the `duckdb-engine` driver baked in, `bi/docker/Dockerfile`)
that boots, migrates its own metadata DB, creates an admin user, and **imports this `bi/` bundle
automatically** (`bi/docker/entrypoint.sh`). No cloud, no extra services (SQLite metadata DB in a
named volume) — stays inside the project's offline régua.

1. Build the marts this bundle reads: `just build` (creates `data/adventureworks.duckdb`).
2. `just bi-up` — builds the image and starts the container (`docker compose up --build -d`).
3. `just bi-logs` to watch the import (takes ~30–60s the first time); it's ready once you see
   gunicorn "Listening at: http://0.0.0.0:8088".
4. Open **http://localhost:8088** — log in with **admin / admin** (override via
   `SUPERSET_ADMIN_USERNAME`/`SUPERSET_ADMIN_PASSWORD` env vars before `just bi-up` if you want a
   different login). Go to **Dashboards → "Adventure Works — Sales"**.
5. `just bi-down` to stop it (keeps the imported state — restart instantly with `just bi-up`
   again); `just bi-reset` to wipe the metadata DB and re-import from a clean slate.

The DuckDB file is mounted **read-only**, and the database connection is configured
`read_only: true` (`bi/databases/adventureworks_duckdb.yaml`'s `extra.engine_params`) — Superset
only ever reads the marts `just build` produced, never writes to them.

### Option B — local Superset install (manual import)
1. Build the marts this bundle reads: `just build` (creates `data/adventureworks.duckdb`).
2. Install Superset locally (not a project dependency — BI-as-code is declarative; Superset
   itself is the runtime, per ADR-0002) and initialize it, e.g.:
   ```
   pip install apache-superset duckdb-engine
   superset db upgrade
   superset fab create-admin
   superset init
   ```
3. Edit `bi/databases/adventureworks_duckdb.yaml`'s `sqlalchemy_uri` to an **absolute** path to
   your checkout's `data/adventureworks.duckdb` (the committed relative form
   `duckdb:///data/adventureworks.duckdb` assumes Superset's working directory is the repo
   root — adjust if not, e.g. `duckdb:////home/you/desafio-ae/data/adventureworks.duckdb`).
4. Import the bundle:
   ```
   superset import-directory bi/
   ```
   (or zip `bi/` and use the Superset UI's "Import" on Databases/Datasets/Charts/Dashboards).

### Once it's running (either option)
Find the five "Hero KPI: …" charts under Charts — each renders the metric declared in
`datasets/main/fct_sales.yaml` (first four) or `datasets/main/vw_promotion_reason_sales.yaml`
(Promotion-Impact Revenue). Also find "Question a: Orders / Quantity / Value by Product" and
"...by Sales Reason" (P4-02), "Question b: Top Products by Average Order Value" (P4-03),
"Question c: Top 10 Customers by Total Transaction Value" (P4-04), "Question d: Top 5 Cities by
Revenue" (P4-05), "Question e: Orders, Quantity & Value by Month/Year" (P4-06), and "Question f:
Top Product -- On Promotion" (P4-07, answers `CHALLENGE.md` question f) under Charts.

Open **Dashboards → "Adventure Works — Sales"** (`bi/dashboards/adventure_works_sales.yaml`,
`P4-08`) to see every chart above assembled onto one page, with the dashboard-wide Sales
Channel / Product / Card Type / Sales Reason / Order Date / Customer / Order Status / City /
State / Country filters (`FR-7`) in the filter bar — narrowing any one of them reshapes every
chart and hero KPI on the dashboard at once (Superset native cross-filter scoping).

## Verifying reconciliation without a running Superset

`scripts/validate_hero_kpis.py` is the outer BDD test for the P4-01 hero tiles;
`scripts/validate_question_f.py` is the outer BDD test for question f + the Promotion-Impact
hero KPI (P4-07). Both read the chart/dataset YAML straight from `bi/` and assert the declared
metric SQL equals a direct aggregate computed against the built DuckDB file directly (no live
Superset server required):

```
uv run python scripts/validate_hero_kpis.py
uv run python scripts/validate_question_f.py
```

`scripts/validate_question_b.py` is the outer BDD test for the P4-03 question-b chart: it picks a
non-vacuous `(year, state)` fixture (a combo backed by real order volume), runs the chart's own
declared virtual-dataset SQL + `average_order_value` metric grouped by product under that filter to
find the top-ranked product, then asserts its AOV equals a direct `fct_sales` aggregate for that
exact product/year/state, joined to `dim_product`, `dim_date`, and `dim_geography` (ship-to,
ADR-0005) and written independently of the `bi/` YAML:

```
uv run python scripts/validate_question_b.py
```

`scripts/test_top10_customers.py` is the outer BDD test for the P4-04 question-c chart: it
checks the chart is configured to return exactly 10 rows ranked descending, and that the top
customer's value reconciles to a direct `fct_sales`/`dim_customer` aggregate:

```
uv run python scripts/test_top10_customers.py
```

`scripts/validate_top5_cities.py` is the outer BDD test for question d (`P4-05`): it re-executes the
`question_d_top_cities` dataset SQL + the `question_d_top5_cities` chart's groupby/metric/row_limit
against the built DuckDB file and asserts exactly 5 distinct cities come back, ranked descending,
with the top city reconciling to a direct `fct_sales` joined `dim_geography` (ship-to, ADR-0005)
aggregate:

```
uv run python scripts/validate_top5_cities.py
```

`scripts/validate_question_e_timeseries.py` is the outer BDD test for the question-e time series
(P4-06): it reads the `question_e_sales_by_month` dataset's declared metric SQL and the chart's
declared metrics, and for every year-month point asserts they reconcile exactly to a direct
`fct_sales` x `dim_date` aggregate written independently, and that the series covers the full
gap-free order-date range (`dim_date` is a day-grain date_spine over exactly that range,
ADR-0006):

```
uv run python scripts/validate_question_e_timeseries.py
```

`scripts/validate_question_a.py` (above) is the outer BDD test for the P4-02 question-a
datasets/charts.

## Documented metric definitions (hero KPIs)

| Metric (`metric_name`) | Dataset | Expression | ADR / source |
|---|---|---|---|
| `total_sales_revenue` | `fct_sales` | `SUM(gross_revenue)` | ADR-0001 |
| `number_of_orders` | `fct_sales` | `COUNT(DISTINCT sales_order_number)` | ARCHITECTURE.md §fct_sales |
| `units_sold` | `fct_sales` | `SUM(order_qty)` | ARCHITECTURE.md §fct_sales |
| `average_order_value` (hero KPI) | `fct_sales` | `(SUM(gross_revenue) - SUM(discount_amount)) / COUNT(DISTINCT sales_order_number)` | ARCHITECTURE.md §fct_sales |
| `average_order_value` (question b) | `question_b_product_aov` | same formula, per product/month/year/city/state/country group | ARCHITECTURE.md §fct_sales; CHALLENGE.md question b |
| `promotion_impact` | `vw_promotion_reason_sales` | `SUM(gross_revenue)` filtered to `sales_reason_name = "On Promotion"` over the `fct_sales`/`bridge_order_sales_reason`/`dim_sales_reason` join (no fan-out, ADR-0003) | ADR-0003, P4-07 |

**Promotion-Impact metric choice (P4-07):** uses `gross_revenue`, not `discount_amount`. The EDA
notebook (`P4-09`) found `discount_amount` sits entirely on the reseller/store channel (60,919
lines), zero on the 60,398 online lines — while the `"On Promotion"` sales-reason tag is
exclusively attached to online orders. `sum(discount_amount)` over the Promotion join is
therefore structurally zero; `sum(gross_revenue)` (the dollar value of orders customers *say*
were driven by a promotion) is the meaningful, non-degenerate "impact" figure and reconciles to
`$6,361,828.95` — the same number the EDA notebook derived independently from the bridge join.

**Question f filter value:** `sales_reason_name = "On Promotion"` is the real `dim_sales_reason`
row (`sales_reason_type = "Promotion"` also matches, non-vacuously). The bare literal
`"Promotion"` matches zero rows — a bug in P3-04's original singular test, fixed on `develop`
(PR #22) before this issue was picked up; this issue's scenario and dataset use the corrected,
real value throughout.

## Documented metric definitions (business questions)

| Question | Metric (`metric_name`) | Expression | Gross vs. net | ADR / source |
|---|---|---|---|---|
| a — orders/qty/value sliced and filtered | `number_of_orders` / `units_purchased` / `total_transaction_value` (`question_a_sales_detail`, `question_a_sales_by_reason`) | `COUNT(DISTINCT sales_order_number)` / `SUM(order_qty)` / `SUM(gross_revenue)` | **Gross** (same convention as the hero KPIs) | ADR-0001 |
| c — top-10 customers by revenue | `total_transaction_value` (`question_c_top10_customers`) | `SUM(gross_revenue)` | **Gross** — chosen to match the P4-01 hero KPI "Total Sales Revenue" and the régua's own headline reconciliation figure (2011 all-channel gross = $12,646,112.16); no parallel net-revenue ranking is introduced | ADR-0001 |
| d — top-5 cities by revenue | `total_transaction_value` (`question_d_top_cities`) | `SUM(gross_revenue)` | **Gross** — same definition as the P4-01 hero KPI "Total Sales Revenue" and question c's `total_transaction_value` (NFR-3, one definition across the dashboard) | ADR-0001 |
| e — orders/qty/value by month & year | `monthly_order_count` / `monthly_quantity` / `monthly_value` (`question_e_sales_by_month`) | `COUNT(DISTINCT sales_order_number)` / `SUM(order_qty)` / `SUM(gross_revenue)` | **Gross** (same convention as above) — grouped by `year_month` (from `dim_date`, ADR-0006's gap-free day-grain `date_spine`) over `fct_sales` joined to `dim_date` on `date_key` | ADR-0001, ADR-0006 |
| f — top product by units for "On Promotion" | `units` (`vw_promotion_reason_sales`) | `SUM(order_qty)` | n/a (units, not revenue) | ADR-0003 |
