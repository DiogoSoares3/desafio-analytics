# bi/ — Apache Superset BI-as-code (ADR-0002)

Committed export of the Superset assets (database connection, datasets, charts, and — from
`P4-08` on — the dashboard) that read the local DuckDB marts built by `just build`. No parallel
metric layer: every metric expression here is the same formula `ARCHITECTURE.md` §fct_sales
defines, and `scripts/validate_hero_kpis.py` proves it reconciles to a direct `fct_sales`
aggregate (NFR-3).

## Layout

```
bi/
  metadata.yaml                          # Superset asset-bundle manifest
  databases/adventureworks_duckdb.yaml   # SQLAlchemy connection -> local DuckDB file
  datasets/main/fct_sales.yaml           # fct_sales dataset + declared metrics
  charts/hero_*.yaml                     # the four P4-01 hero-KPI tiles (big_number_total)
```
Later issues (P4-02–P4-08) add datasets/charts for the six business questions and assemble a
`dashboards/*.yaml`.

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
   declared in `datasets/main/fct_sales.yaml`.

## Verifying reconciliation without a running Superset

`scripts/validate_hero_kpis.py` is the outer BDD test for this bundle: it reads each hero chart's
declared metric SQL straight from this YAML and asserts it equals a direct `fct_sales` aggregate,
computed against the built DuckDB file directly (no live Superset server required):

```
uv run python scripts/validate_hero_kpis.py
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
