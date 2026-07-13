# bi/ — Apache Superset BI-as-code (ADR-0002)

Committed export of the Superset assets (database connection, datasets, charts, and — from
`P4-08` on — the dashboard) that read the local DuckDB marts built by `just build`. No parallel
metric layer: every metric expression here is the same formula `ARCHITECTURE.md` §fct_sales
defines, and `scripts/validate_hero_kpis.py` proves it reconciles to a direct `fct_sales`
aggregate (NFR-3).

## Layout

```
bi/
  metadata.yaml                                    # Superset asset-bundle manifest
  databases/adventureworks_duckdb.yaml             # SQLAlchemy connection -> local DuckDB file
  datasets/main/fct_sales.yaml                     # fct_sales dataset + declared metrics
  datasets/main/question_c_top10_customers.yaml    # P4-04 -- question-c virtual dataset
  datasets/main/question_e_sales_by_month.yaml     # P4-06 -- question-e virtual dataset (fct_sales x dim_date)
  datasets/main/vw_promotion_reason_sales.yaml     # P4-07 -- virtual (SQL) dataset for question f
  charts/hero_*.yaml                               # the five hero-KPI tiles (big_number_total)
  charts/question_c_top10_customers.yaml           # P4-04 -- top-10-customers table chart
  charts/question_e_orders_qty_value_by_month.yaml # P4-06 -- question-e time-series chart
  charts/question_f_top_product_promotion.yaml     # P4-07 -- question f: top product, "On Promotion"
```
Later issues (P4-02, P4-03, P4-05, P4-08) add datasets/charts for the remaining business
questions and assemble a `dashboards/*.yaml`.

## Run instructions (local import)

1. Build the marts this bundle reads: `just build` (creates `data/adventureworks.duckdb`).
2. Install Superset locally (not a project dependency — BI-as-code is declarative; Superset
   itself is the runtime, per ADR-0002) and initialize it, e.g.:
   ```
   pip install apache-superset
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
5. Open Superset, find the five "Hero KPI: …" charts under Charts — each renders the metric
   declared in `datasets/main/fct_sales.yaml` (first four) or
   `datasets/main/vw_promotion_reason_sales.yaml` (Promotion-Impact Revenue). Also find
   "Question c: Top 10 Customers by Total Transaction Value" (P4-04), "Question e: Orders,
   Quantity & Value by Month/Year" (P4-06), and "Question f: Top Product -- On Promotion"
   (P4-07, answers `CHALLENGE.md` question f) under Charts.

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

`scripts/test_top10_customers.py` is the outer BDD test for the P4-04 question-c chart: it
checks the chart is configured to return exactly 10 rows ranked descending, and that the top
customer's value reconciles to a direct `fct_sales`/`dim_customer` aggregate:

```
uv run python scripts/test_top10_customers.py
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

## Documented metric definitions (hero KPIs)

| Metric (`metric_name`) | Expression | ADR / source |
|---|---|---|
| `total_sales_revenue` | `SUM(gross_revenue)` | ADR-0001 |
| `number_of_orders` | `COUNT(DISTINCT sales_order_number)` | ARCHITECTURE.md §fct_sales |
| `units_sold` | `SUM(order_qty)` | ARCHITECTURE.md §fct_sales |
| `average_order_value` | `(SUM(gross_revenue) - SUM(discount_amount)) / COUNT(DISTINCT sales_order_number)` | ARCHITECTURE.md §fct_sales |
| `promotion_impact` | `SUM(gross_revenue)` filtered to `sales_reason_name = "On Promotion"` over the `fct_sales`/`bridge_order_sales_reason`/`dim_sales_reason` join (no fan-out, ADR-0003) | ADR-0003, P4-07 |

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
| c — top-10 customers by revenue | `total_transaction_value` (`question_c_top10_customers`) | `SUM(gross_revenue)` | **Gross** — chosen to match the P4-01 hero KPI "Total Sales Revenue" and the régua's own headline reconciliation figure (2011 all-channel gross = $12,646,112.16); no parallel net-revenue ranking is introduced | ADR-0001 |
| e — orders/qty/value by month & year | `monthly_order_count` / `monthly_quantity` / `monthly_value` (`question_e_sales_by_month`) | `COUNT(DISTINCT sales_order_number)` / `SUM(order_qty)` / `SUM(gross_revenue)` | **Gross** (same convention as above) — grouped by `year_month` (from `dim_date`, ADR-0006's gap-free day-grain `date_spine`) over `fct_sales` joined to `dim_date` on `date_key` | ADR-0001, ADR-0006 |
| f — top product by units for "On Promotion" | `units` (`vw_promotion_reason_sales`) | `SUM(order_qty)` | n/a (units, not revenue) | ADR-0003 |
