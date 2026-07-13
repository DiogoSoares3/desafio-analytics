"""Outer behaviour test (P4-01) -- hero KPI tiles reconcile to fct_sales.

Realizes the P4-01 Gherkin scenario (docs/phases/phase-4/backlog.md): each hero-KPI tile exported
under ``bi/`` as a Superset dataset **metric** (BI-as-code, ADR-0002) must compute the *exact same*
number as a direct aggregate query written independently against the built ``fct_sales`` mart --
proving there is no parallel metric layer (NFR-3). This is the phase's seam: no dbt test exists for
Phase 4, so the reconciliation check itself is the outer test (ARCHITECTURE.md SS BI).

Usage
-----
    uv run python scripts/validate_hero_kpis.py

Exits non-zero (and prints which KPI mismatched or which file is missing) on failure -- this is a
test, not a report. RED before ``bi/datasets/main/fct_sales.yaml`` and the four hero chart YAML
files exist (FileNotFoundError -- the feature is absent); GREEN once the ``bi/`` scaffold is built
and its declared metric SQL expressions agree with fct_sales.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"
DATASET_YAML = BI_DIR / "datasets" / "main" / "fct_sales.yaml"

HERO_CHARTS = {
    "Total Sales Revenue": BI_DIR / "charts" / "hero_total_sales_revenue.yaml",
    "Number of Orders": BI_DIR / "charts" / "hero_number_of_orders.yaml",
    "Units Sold": BI_DIR / "charts" / "hero_units_sold.yaml",
    "Average Order Value": BI_DIR / "charts" / "hero_average_order_value.yaml",
}

# Direct aggregates over fct_sales, written independently of the bi/ YAML -- the reconciliation
# oracle the Gherkin scenario asserts against (docs/phases/phase-4/backlog.md P4-01).
DIRECT_AGGREGATE_SQL = {
    "Total Sales Revenue": "select sum(gross_revenue) from fct_sales",
    "Number of Orders": "select count(distinct sales_order_number) from fct_sales",
    "Units Sold": "select sum(order_qty) from fct_sales",
    "Average Order Value": (
        "select (sum(gross_revenue) - sum(discount_amount)) / "
        "count(distinct sales_order_number) from fct_sales"
    ),
}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(f"{rel} does not exist -- the bi/ scaffold has not been built yet")
    return yaml.safe_load(path.read_text())


def dataset_metric_sql(dataset: dict, metric_name: str) -> str:
    for metric in dataset.get("metrics", []):
        if metric.get("metric_name") == metric_name:
            return metric["expression"]
    raise KeyError(f"metric '{metric_name}' not declared in {DATASET_YAML.name}")


def chart_metric_name(chart: dict) -> str:
    params = chart.get("params", {})
    metric = params.get("metric")
    if isinstance(metric, dict):
        return metric["label"]
    return metric


def main() -> int:
    dataset = load_yaml(DATASET_YAML)

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    failures: list[str] = []
    for kpi_label, chart_path in HERO_CHARTS.items():
        chart = load_yaml(chart_path)
        metric_name = chart_metric_name(chart)
        metric_sql = dataset_metric_sql(dataset, metric_name)

        exported_row = con.execute(f"select {metric_sql} from fct_sales").fetchone()
        direct_row = con.execute(DIRECT_AGGREGATE_SQL[kpi_label]).fetchone()
        assert exported_row is not None and direct_row is not None
        exported_value = exported_row[0]
        direct_value = direct_row[0]

        match = round(float(exported_value), 2) == round(float(direct_value), 2)
        status = "OK" if match else "MISMATCH"
        print(
            f"[{status}] {kpi_label}: exported metric ({metric_name!r}) = {exported_value!r} | "
            f"direct fct_sales aggregate = {direct_value!r}"
        )
        if not match:
            failures.append(kpi_label)

    con.close()

    if failures:
        print(
            f"\nFAILED: {len(failures)} hero KPI(s) did not reconcile: {failures}", file=sys.stderr
        )
        return 1

    print(
        f"\nPASSED: all {len(HERO_CHARTS)} hero KPI tiles reconcile to direct fct_sales aggregates."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
