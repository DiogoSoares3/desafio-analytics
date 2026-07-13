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
  charts/hero_*.yaml                               # the four P4-01 hero-KPI tiles (big_number_total)
  charts/question_c_top10_customers.yaml           # P4-04 -- top-10-customers table chart
  charts/question_e_orders_qty_value_by_month.yaml # P4-06 -- question-e time-series chart
```
Later issues (P4-02–P4-03, P4-05, P4-07–P4-08) add datasets/charts for the remaining business
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
5. Open Superset, find the four "Hero KPI: …" charts under Charts — each renders the metric
   declared in `datasets/main/fct_sales.yaml`. Find "Question c: Top 10 Customers by Total
   Transaction Value" under Charts for the P4-04 question-c chart, and "Question e: Orders,
   Quantity & Value by Month/Year" for the P4-06 time series.

## Verifying reconciliation without a running Superset

`scripts/validate_hero_kpis.py` is the outer BDD test for the P4-01 bundle: it reads each hero
chart's declared metric SQL straight from this YAML and asserts it equals a direct `fct_sales`
aggregate, computed against the built DuckDB file directly (no live Superset server required):

```
uv run python scripts/validate_hero_kpis.py
```

`scripts/validate_top10_customers.py` is the outer BDD test for the P4-04 question-c chart: it
checks the chart is configured to return exactly 10 rows ranked descending, and that the top
customer's value reconciles to a direct `fct_sales`/`dim_customer` aggregate:

```
uv run python scripts/validate_top10_customers.py
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

The fifth hero KPI (Promotion-impact, `FR-8`) is added in `P4-07` once
`bridge_order_sales_reason` is wired into a dataset.

## Documented metric definitions (business questions)

| Question | Metric (`metric_name`) | Expression | Gross vs. net | ADR / source |
|---|---|---|---|---|
| c — top-10 customers by revenue | `total_transaction_value` (`question_c_top10_customers`) | `SUM(gross_revenue)` | **Gross** — chosen to match the P4-01 hero KPI "Total Sales Revenue" and the régua's own headline reconciliation figure (2011 all-channel gross = $12,646,112.16); no parallel net-revenue ranking is introduced | ADR-0001 |
| e — orders/qty/value by month & year | `monthly_order_count` / `monthly_quantity` / `monthly_value` (`question_e_sales_by_month`) | `COUNT(DISTINCT sales_order_number)` / `SUM(order_qty)` / `SUM(gross_revenue)` | **Gross** (same convention as above) — grouped by `year_month` (from `dim_date`, ADR-0006's gap-free day-grain `date_spine`) over `fct_sales` joined to `dim_date` on `date_key` | ADR-0001, ADR-0006 |
