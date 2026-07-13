"""Outer behaviour test (P4-03) -- top products by AOV reconciles to fct_sales.

Realizes the P4-03 Gherkin scenario (docs/phases/phase-4/backlog.md):

    Scenario: top products by AOV reconciles to a direct fct_sales computation
      Given the Superset datasets registered in P4-01
      When I render the question-b chart filtered to a specific year and state
      Then the top-ranked product's AOV equals (sum(gross_revenue) - sum(discount_amount)) /
        count(distinct sales_order_number) computed directly over fct_sales for that product,
        year, and state

Follows the P4-01 pattern (``scripts/validate_hero_kpis.py``): read the question-b dataset/chart
declared under ``bi/`` (BI-as-code, ADR-0002), run the chart's own SQL/metric under a year+state
filter to find the top-ranked product, then assert its AOV matches a direct aggregate over
``fct_sales`` (joined to ``dim_product``, ``dim_date``, ``dim_geography`` -- ship-to, ADR-0005)
written independently -- no parallel metric layer (NFR-3).

Usage
-----
    uv run python scripts/validate_question_b.py

Exits non-zero on mismatch or on a missing bi/ file. RED before
``bi/datasets/main/question_b_product_aov.yaml`` and
``bi/charts/question_b_top_products_by_aov.yaml`` exist (FileNotFoundError -- the feature is
absent); GREEN once the question-b dataset/chart YAML are built and their declared SQL/metric
agree with fct_sales.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"
DATASET_YAML = BI_DIR / "datasets" / "main" / "question_b_product_aov.yaml"
CHART_YAML = BI_DIR / "charts" / "question_b_top_products_by_aov.yaml"

AOV_METRIC_NAME = "average_order_value"

# Minimum distinct orders a (year, state) combo must have for the reconciliation check to be
# non-vacuous (mirrors the P4-09 EDA finding: a vacuous NULL == NULL comparison proves nothing).
MIN_ORDERS_FOR_FIXTURE = 5


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(
            f"{rel} does not exist -- the question-b bi/ assets are not built yet"
        )
    return yaml.safe_load(path.read_text())


def dataset_metric_sql(dataset: dict, metric_name: str) -> str:
    for metric in dataset.get("metrics", []):
        if metric.get("metric_name") == metric_name:
            return metric["expression"]
    raise KeyError(f"metric '{metric_name}' not declared in {DATASET_YAML.name}")


def chart_metric_name(chart: dict) -> str:
    params = chart.get("params", {})
    # Table-viz charts (this one) declare a `metrics` list; big_number_total charts (P4-01) declare
    # a single `metric`. Support both so this helper works for either viz_type.
    metric = params.get("metric")
    if metric is None:
        metrics = params.get("metrics") or []
        metric = metrics[0] if metrics else None
    if isinstance(metric, dict):
        return metric["label"]
    if metric is None:
        raise KeyError(f"chart {CHART_YAML.name} declares no 'metric'/'metrics'")
    return metric


def chart_groupby_column(chart: dict) -> str:
    params = chart.get("params", {})
    groupby = params.get("groupby") or []
    if not groupby:
        raise KeyError(f"chart {CHART_YAML.name} declares no groupby column")
    return groupby[0]


def pick_non_vacuous_fixture(con: duckdb.DuckDBPyConnection, dataset_sql: str) -> tuple[int, str]:
    """Pick a (year, state_province) combo backed by real order volume.

    Written independently of the chart config -- avoids the P4-09-flagged vacuous-pass trap
    (asserting equality of two NULLs proves nothing).
    """
    row = con.execute(
        f"""
        with base as ({dataset_sql})
        select year, state_province, count(distinct sales_order_number) as order_count
        from base
        group by year, state_province
        order by order_count desc
        limit 1
        """
    ).fetchone()
    if row is None or row[2] < MIN_ORDERS_FOR_FIXTURE:
        raise AssertionError("no (year, state) fixture with enough distinct orders was found")
    return int(row[0]), str(row[1])


def main() -> int:
    dataset = load_yaml(DATASET_YAML)
    chart = load_yaml(CHART_YAML)

    dataset_sql = dataset.get("sql")
    if not dataset_sql:
        raise KeyError(f"{DATASET_YAML.name} declares no virtual-dataset 'sql'")

    metric_name = chart_metric_name(chart)
    if metric_name != AOV_METRIC_NAME:
        raise AssertionError(
            f"expected the question-b chart to use metric {AOV_METRIC_NAME!r}, got {metric_name!r}"
        )
    metric_sql = dataset_metric_sql(dataset, metric_name)
    groupby_col = chart_groupby_column(chart)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    year, state_province = pick_non_vacuous_fixture(con, dataset_sql)
    print(f"Fixture: year={year}, state_province={state_province!r}")

    # "Render the question-b chart filtered to a specific year and state" -- the chart's own
    # declared SQL/metric, grouped by product, ranked by AOV, under the fixture's filter.
    exported_row = con.execute(
        f"""
        with base as ({dataset_sql})
        select {groupby_col}, {metric_sql} as aov, count(distinct sales_order_number) as order_count
        from base
        where year = ? and state_province = ?
        group by {groupby_col}
        order by aov desc
        limit 1
        """,
        [year, state_province],
    ).fetchone()
    assert exported_row is not None, "chart query returned no top-ranked product for the fixture"
    top_product, exported_aov, _order_count = exported_row
    print(f"Top-ranked product (chart query): {top_product!r} -> AOV = {exported_aov!r}")

    # Direct aggregate over fct_sales for that exact product/year/state, written independently
    # of the bi/ YAML -- the reconciliation oracle the Gherkin scenario asserts against.
    direct_row = con.execute(
        """
        select
            (sum(fct_sales.gross_revenue) - sum(fct_sales.discount_amount))
            / count(distinct fct_sales.sales_order_number) as aov
        from fct_sales
        inner join dim_product on fct_sales.product_key = dim_product.product_key
        inner join dim_date on fct_sales.date_key = dim_date.date_key
        inner join dim_geography on fct_sales.geography_key = dim_geography.geography_key
        where dim_product.product_name = ?
          and dim_date.year = ?
          and dim_geography.state_province = ?
        """,
        [top_product, year, state_province],
    ).fetchone()
    assert direct_row is not None
    direct_aov = direct_row[0]
    print(f"Direct fct_sales aggregate for {top_product!r}: AOV = {direct_aov!r}")

    con.close()

    match = round(float(exported_aov), 2) == round(float(direct_aov), 2)
    status = "OK" if match else "MISMATCH"
    print(f"\n[{status}] top-ranked product AOV (year={year}, state={state_province!r})")

    if not match:
        print(
            f"\nFAILED: question-b top product {top_product!r} AOV did not reconcile "
            f"(chart={exported_aov!r} vs direct={direct_aov!r})",
            file=sys.stderr,
        )
        return 1

    print("\nPASSED: question-b top-ranked product AOV reconciles to a direct fct_sales aggregate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
