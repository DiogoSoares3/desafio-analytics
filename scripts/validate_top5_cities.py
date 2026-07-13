"""Outer behaviour test (P4-05) -- top-5-cities chart reconciles to fct_sales joined dim_geography.

Realizes the P4-05 Gherkin scenario (docs/phases/phase-4/backlog.md, "Question d: top-5 cities by
revenue"): the question-d chart exported under ``bi/`` (BI-as-code, ADR-0002) must (1) list exactly
5 distinct cities ranked descending by total transaction value and (2) the top city's value must
equal a direct aggregate over ``fct_sales`` joined to ``dim_geography`` (ship-to, ADR-0005),
computed independently of the ``bi/`` YAML -- proving no parallel metric layer (NFR-3). Mirrors
``scripts/validate_hero_kpis.py``'s pattern: reads the declared dataset SQL + chart
groupby/metric/row_limit straight from the committed YAML and re-executes them against the built
DuckDB file directly -- no live Superset server required (this phase's seam per
ARCHITECTURE.md SS BI).

Usage
-----
    uv run python scripts/validate_top5_cities.py

Exits non-zero (and prints why) on failure -- this is a test, not a report. RED before
``bi/datasets/main/question_d_top_cities.yaml`` and ``bi/charts/question_d_top5_cities.yaml`` exist
(FileNotFoundError -- the feature is absent); GREEN once the P4-05 bi/ scaffold is built and its
declared query reconciles to the direct fct_sales/dim_geography aggregate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"
DATASET_YAML = BI_DIR / "datasets" / "main" / "question_d_top_cities.yaml"
CHART_YAML = BI_DIR / "charts" / "question_d_top5_cities.yaml"

EXPECTED_TOP_N = 5

# Direct aggregate over fct_sales joined to dim_geography (ship-to, ADR-0005), written independently
# of the bi/ YAML -- the reconciliation oracle the P4-05 Gherkin scenario asserts against.
DIRECT_TOP_CITY_SQL = """
    select dim_geography.city, sum(fct_sales.gross_revenue) as total_transaction_value
    from fct_sales
    inner join dim_geography
        on fct_sales.geography_key = dim_geography.geography_key
    group by dim_geography.city
    order by total_transaction_value desc
    limit 1
"""


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(
            f"{rel} does not exist -- the P4-05 bi/ scaffold has not been built yet"
        )
    return yaml.safe_load(path.read_text())


def dataset_metric_sql(dataset: dict, metric_name: str) -> str:
    for metric in dataset.get("metrics", []):
        if metric.get("metric_name") == metric_name:
            return metric["expression"]
    raise KeyError(f"metric '{metric_name}' not declared in {DATASET_YAML.name}")


def chart_query_spec(chart: dict) -> tuple[str, str, int]:
    """Return (groupby_column, metric_name, row_limit) declared on the chart."""
    params = chart.get("params", {})
    groupby = params["groupby"]
    groupby_col = groupby[0] if isinstance(groupby, list) else groupby
    metrics = params["metrics"]
    metric_name = metrics[0] if isinstance(metrics, list) else metrics
    if isinstance(metric_name, dict):
        metric_name = metric_name["label"]
    row_limit = int(params["row_limit"])
    return groupby_col, metric_name, row_limit


def main() -> int:
    dataset = load_yaml(DATASET_YAML)
    chart = load_yaml(CHART_YAML)

    dataset_sql = dataset["sql"]
    groupby_col, metric_name, row_limit = chart_query_spec(chart)
    metric_expr = dataset_metric_sql(dataset, metric_name)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    chart_query = f"""
        select {groupby_col}, {metric_expr} as value
        from ({dataset_sql}) as question_d_top_cities
        group by {groupby_col}
        order by value desc
        limit {row_limit}
    """
    chart_rows = con.execute(chart_query).fetchall()

    direct_row = con.execute(DIRECT_TOP_CITY_SQL).fetchone()
    con.close()

    failures: list[str] = []

    distinct_cities = {row[0] for row in chart_rows}
    if len(chart_rows) != EXPECTED_TOP_N or len(distinct_cities) != EXPECTED_TOP_N:
        failures.append(
            f"expected exactly {EXPECTED_TOP_N} distinct cities, got {len(chart_rows)} rows / "
            f"{len(distinct_cities)} distinct: {chart_rows}"
        )

    is_ranked_desc = all(
        chart_rows[i][1] >= chart_rows[i + 1][1] for i in range(len(chart_rows) - 1)
    )
    if not is_ranked_desc:
        failures.append(f"chart rows are not ranked descending by value: {chart_rows}")

    assert direct_row is not None
    direct_city, direct_value = direct_row

    if chart_rows:
        chart_top_city, chart_top_value = chart_rows[0]
        if chart_top_city != direct_city:
            failures.append(
                f"top city mismatch: chart={chart_top_city!r} vs direct aggregate={direct_city!r}"
            )
        elif round(float(chart_top_value), 2) != round(float(direct_value), 2):
            failures.append(
                f"top city value mismatch for {chart_top_city!r}: chart={chart_top_value!r} vs "
                f"direct fct_sales/dim_geography aggregate={direct_value!r}"
            )

    print(f"chart rows (top {row_limit} by {metric_name}): {chart_rows}")
    print(f"direct fct_sales/dim_geography aggregate top city: {direct_city!r} = {direct_value!r}")

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) did not pass:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(
        f"\nPASSED: question-d chart lists exactly {EXPECTED_TOP_N} cities ranked descending by "
        "total transaction value, and the top city reconciles to a direct fct_sales/dim_geography "
        "aggregate (ship-to, ADR-0005)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
