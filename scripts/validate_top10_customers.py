"""Outer behaviour test (P4-04) -- top-10 customers by revenue reconciles to fct_sales.

Realizes the P4-04 Gherkin scenario (docs/phases/phase-4/backlog.md): the question-c chart
(BI-as-code, ADR-0002) ranking dim_customer by total transaction value must (1) be configured to
return exactly 10 rows, ranked descending, and (2) its top-ranked customer's value must equal a
direct aggregate over fct_sales joined to dim_customer, computed independently of the chart/dataset
YAML -- proving there is no parallel metric layer (NFR-3). This is the phase's seam: no dbt test
exists for Phase 4, so the reconciliation check itself is the outer test (ARCHITECTURE.md SS BI).

Metric choice (documented, ADR-0001): "total transaction value" here is **gross revenue**
(sum(gross_revenue), pre-discount/pre-tax/pre-freight), consistent with the P4-01 hero KPI "Total
Sales Revenue" and the régua's own headline figure (2011 gross = $12,646,112.16). No parallel
"net revenue" ranking is introduced for this slice.

Usage
-----
    uv run python scripts/validate_top10_customers.py

Exits non-zero (and prints what mismatched or which file is missing) on failure -- this is a test,
not a report. RED before bi/datasets/main/question_c_top10_customers.yaml and
bi/charts/question_c_top10_customers.yaml exist (FileNotFoundError -- the feature is absent); GREEN
once the chart/dataset YAML land and reconcile to a direct fct_sales/dim_customer aggregate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"
DATASET_YAML = BI_DIR / "datasets" / "main" / "question_c_top10_customers.yaml"
CHART_YAML = BI_DIR / "charts" / "question_c_top10_customers.yaml"

EXPECTED_ROW_COUNT = 10

# Direct aggregate over fct_sales joined to dim_customer, written independently of the bi/ YAML --
# the reconciliation oracle the Gherkin scenario asserts against (docs/phases/phase-4/backlog.md
# P4-04). "Total transaction value" = gross revenue (see module docstring).
DIRECT_TOP10_SQL = """
    select
        c.full_name,
        sum(f.gross_revenue) as total_transaction_value
    from fct_sales f
    inner join dim_customer c on f.customer_key = c.customer_key
    group by c.full_name
    order by total_transaction_value desc
    limit 10
"""


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(
            f"{rel} does not exist -- the question-c chart has not been built yet"
        )
    return yaml.safe_load(path.read_text())


def dataset_metric_sql(dataset: dict, metric_name: str) -> str:
    for metric in dataset.get("metrics", []):
        if metric.get("metric_name") == metric_name:
            return metric["expression"]
    raise KeyError(f"metric '{metric_name}' not declared in {DATASET_YAML.name}")


def dataset_sql(dataset: dict) -> str:
    sql = dataset.get("sql")
    if not sql:
        raise KeyError(f"{DATASET_YAML.name} does not declare a virtual dataset 'sql:' query")
    return sql


def chart_metric_name(chart: dict) -> str:
    params = chart.get("params", {})
    metric = params.get("metric")
    if isinstance(metric, dict):
        return metric["label"]
    return metric


def chart_groupby_column(chart: dict) -> str:
    params = chart.get("params", {})
    groupby = params.get("groupby") or []
    if not groupby:
        raise KeyError(
            "question-c chart does not declare a 'groupby' column (expected customer name)"
        )
    return groupby[0]


def main() -> int:
    dataset = load_yaml(DATASET_YAML)
    chart = load_yaml(CHART_YAML)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    failures: list[str] = []

    # 1. Chart config: exactly EXPECTED_ROW_COUNT rows, ranked descending.
    params = chart.get("params", {})
    row_limit = params.get("row_limit")
    order_desc = params.get("order_desc")
    if row_limit != EXPECTED_ROW_COUNT:
        failures.append(f"row_limit = {row_limit!r}, expected {EXPECTED_ROW_COUNT}")
    if order_desc is not True:
        failures.append(f"order_desc = {order_desc!r}, expected True (ranked descending)")

    # 2. Reconciliation: run the declared dataset SQL (the chart's data source), aggregate/rank it
    #    exactly as the chart does, and compare the top row against the independent direct query.
    metric_name = chart_metric_name(chart)
    metric_sql = dataset_metric_sql(dataset, metric_name)
    groupby_col = chart_groupby_column(chart)
    sql = dataset_sql(dataset)

    exported_query = f"""
        with question_c as ({sql})
        select {groupby_col}, {metric_sql} as value
        from question_c
        group by {groupby_col}
        order by value desc
        limit {EXPECTED_ROW_COUNT}
    """
    exported_rows = con.execute(exported_query).fetchall()
    direct_rows = con.execute(DIRECT_TOP10_SQL).fetchall()

    if len(exported_rows) != EXPECTED_ROW_COUNT:
        failures.append(
            f"exported query returned {len(exported_rows)} rows, expected {EXPECTED_ROW_COUNT}"
        )
    if len(direct_rows) != EXPECTED_ROW_COUNT:
        failures.append(
            f"direct oracle query returned {len(direct_rows)} rows, expected {EXPECTED_ROW_COUNT}"
        )

    if exported_rows and direct_rows:
        top_exported_name, top_exported_value = exported_rows[0]
        top_direct_name, top_direct_value = direct_rows[0]
        name_match = top_exported_name == top_direct_name
        value_match = round(float(top_exported_value), 2) == round(float(top_direct_value), 2)
        status = "OK" if (name_match and value_match) else "MISMATCH"
        print(
            f"[{status}] top customer: exported = "
            f"({top_exported_name!r}, {top_exported_value!r}) | "
            f"direct fct_sales/dim_customer aggregate = "
            f"({top_direct_name!r}, {top_direct_value!r})"
        )
        if not name_match:
            failures.append(
                f"top customer name mismatch: {top_exported_name!r} != {top_direct_name!r}"
            )
        if not value_match:
            failures.append(
                f"top customer value mismatch: {top_exported_value!r} != {top_direct_value!r}"
            )
    else:
        print("[MISMATCH] could not compare top customer -- one or both queries returned no rows")

    con.close()

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) did not pass:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    print(
        f"\nPASSED: question-c chart lists exactly {EXPECTED_ROW_COUNT} customers ranked by total "
        "transaction value, and the top customer reconciles to a direct fct_sales/dim_customer "
        "aggregate."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
