"""Outer behaviour test (P4-06) -- question-e time series reconciles to fct_sales x dim_date.

Realizes the P4-06 Gherkin scenario (docs/phases/phase-4/backlog.md): the question-e time-series
chart -- CHALLENGE.md question e, "number of orders, quantity purchased, and total transaction value
by month and year" -- must, for every year-month point, compute the *exact same* order count/
quantity/value as a direct aggregate over ``fct_sales`` joined to ``dim_date``, written
independently of the ``bi/`` YAML (no parallel metric layer, NFR-3). It must also cover the full
order-date range with no gaps (``dim_date`` is a gap-free day-grain date_spine over exactly that
range, ADR-0006).

Usage
-----
    uv run python scripts/validate_question_e_timeseries.py

Exits non-zero (and prints the mismatch/gap) on failure -- this is a test, not a report. RED before
``bi/datasets/main/question_e_sales_by_month.yaml`` and the question-e chart YAML exist
(FileNotFoundError -- the feature is absent); GREEN once the ``bi/`` dataset + chart are built and
their declared metric SQL agrees with the direct fct_sales x dim_date aggregate, with no month gaps.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"
DATASET_YAML = BI_DIR / "datasets" / "main" / "question_e_sales_by_month.yaml"
CHART_YAML = BI_DIR / "charts" / "question_e_orders_qty_value_by_month.yaml"

# Metric label -> the metric_name this test expects the chart to declare on the question-e dataset.
REQUIRED_METRICS = {
    "Number of Orders": "monthly_order_count",
    "Quantity Purchased": "monthly_quantity",
    "Total Transaction Value": "monthly_value",
}

# Direct aggregate over fct_sales joined to dim_date, written independently of the bi/ YAML -- the
# reconciliation oracle the Gherkin scenario asserts against (docs/phases/phase-4/backlog.md P4-06).
DIRECT_SERIES_SQL = """
    select
        d.year_month,
        count(distinct f.sales_order_number) as monthly_order_count,
        sum(f.order_qty) as monthly_quantity,
        sum(f.gross_revenue) as monthly_value
    from main.fct_sales as f
    join main.dim_date as d on f.date_key = d.date_key
    group by d.year_month
    order by d.year_month
"""

# The full, gap-free set of calendar months dim_date spans -- ADR-0006 builds dim_date as a
# day-grain date_spine over exactly [min(order_date), max(order_date)], so its distinct year_month
# values ARE the full order-date range with no gaps, by construction.
FULL_RANGE_MONTHS_SQL = "select distinct year_month from main.dim_date order by year_month"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(
            f"{rel} does not exist -- the bi/ question-e slice has not been built yet"
        )
    return yaml.safe_load(path.read_text())


def dataset_metric_sql(dataset: dict, metric_name: str) -> str:
    for metric in dataset.get("metrics", []):
        if metric.get("metric_name") == metric_name:
            return metric["expression"]
    raise KeyError(f"metric '{metric_name}' not declared in {DATASET_YAML.name}")


def chart_metric_names(chart: dict) -> list[str]:
    params = chart.get("params", {})
    metrics = params.get("metrics", params.get("metric"))
    if metrics is None:
        raise KeyError(f"no metric(s) declared on chart {CHART_YAML.name}")
    if isinstance(metrics, str):
        metrics = [metrics]
    names = []
    for metric in metrics:
        names.append(metric["label"] if isinstance(metric, dict) else metric)
    return names


def consecutive_months(year_months: list[str]) -> bool:
    """True iff year_months (sorted 'YYYY-MM' strings) has no skipped calendar month."""
    years_months = [(int(ym[:4]), int(ym[5:7])) for ym in year_months]
    for (y1, m1), (y2, m2) in zip(years_months, years_months[1:], strict=False):
        expected = (y1, m1 + 1) if m1 < 12 else (y1 + 1, 1)
        if (y2, m2) != expected:
            return False
    return True


def main() -> int:
    dataset = load_yaml(DATASET_YAML)
    chart = load_yaml(CHART_YAML)

    dataset_sql = dataset.get("sql")
    if not dataset_sql:
        raise ValueError(
            f"{DATASET_YAML.name} must declare a virtual-dataset 'sql' joining "
            "fct_sales to dim_date"
        )

    declared_names = chart_metric_names(chart)
    missing = set(REQUIRED_METRICS.values()) - set(declared_names)
    if missing:
        raise KeyError(f"chart {CHART_YAML.name} is missing required metric(s): {sorted(missing)}")

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    metric_exprs = {
        metric_name: dataset_metric_sql(dataset, metric_name)
        for metric_name in REQUIRED_METRICS.values()
    }
    exported_sql = (
        "select year_month, "
        + ", ".join(f"{expr} as {name}" for name, expr in metric_exprs.items())
        + f" from ({dataset_sql}) group by year_month order by year_month"
    )
    exported_rows = {row[0]: row[1:] for row in con.execute(exported_sql).fetchall()}
    direct_rows = {row[0]: row[1:] for row in con.execute(DIRECT_SERIES_SQL).fetchall()}

    failures: list[str] = []

    if set(exported_rows) != set(direct_rows):
        failures.append(
            f"year-month point sets differ: exported={sorted(exported_rows)} vs "
            f"direct={sorted(direct_rows)}"
        )

    for year_month in sorted(set(exported_rows) & set(direct_rows)):
        exported_point = exported_rows[year_month]
        direct_point = direct_rows[year_month]
        match = tuple(
            round(float(a), 2) if a is not None else None for a in exported_point
        ) == tuple(round(float(b), 2) if b is not None else None for b in direct_point)
        status = "OK" if match else "MISMATCH"
        print(f"[{status}] {year_month}: exported={exported_point} | direct={direct_point}")
        if not match:
            failures.append(f"{year_month}: exported={exported_point} != direct={direct_point}")

    full_range_months = [row[0] for row in con.execute(FULL_RANGE_MONTHS_SQL).fetchall()]
    series_months = sorted(direct_rows)

    if series_months != full_range_months:
        failures.append(
            "series does not cover the full gap-free order-date range: "
            f"series={series_months} vs dim_date full range={full_range_months}"
        )
    elif not consecutive_months(series_months):
        failures.append(f"series has a skipped calendar month: {series_months}")
    else:
        print(
            f"[OK] series covers the full gap-free range: {series_months[0]} .. {series_months[-1]}"
        )

    con.close()

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(
        f"\nPASSED: question-e time series ({len(series_months)} year-month points) reconciles "
        "exactly to direct fct_sales x dim_date aggregates, no gaps."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
