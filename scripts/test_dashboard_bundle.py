"""Outer behaviour test (P4-08) -- the assembled dashboard bundle is deliverable-equivalent.

Realizes the P4-08 Gherkin scenario (docs/phases/phase-4/backlog.md, "Deliverable-equivalence
packaging"): one committed Superset dashboard (BI-as-code, ADR-0002) assembling every chart from
P4-01-P4-07 (five hero-KPI tiles + the seven business-question charts a-f) must:

1. Reference **every** chart currently exported under ``bi/charts/*.yaml`` -- nothing built in
   P4-01..P4-07 is left off the dashboard.
2. Wire a dashboard-wide native filter set covering the sales-channel filter (``is_online``,
   online/reseller) plus the other ``FR-7`` filters (product, card type, sales reason, order date,
   customer, order status, city, state, country) -- each filter must target a real, filterable
   column on a real, committed dataset.
3. Have every metric used by any dataset the dashboard's charts read documented in
   ``bi/README.md``'s metric-definitions tables (the analogue of documented DAX, ``FR-9``) -- no
   metric on the dashboard is left undocumented.

No live Superset is required (same pattern as ``validate_hero_kpis.py``/``validate_question_a.py``):
this script reads the committed YAML directly and checks it is internally consistent and complete.

Usage
-----
    uv run python scripts/test_dashboard_bundle.py

Exits non-zero on any missing chart/filter/doc gap -- this is a test, not a report. RED before
``bi/dashboards/adventure_works_sales.yaml`` exists (FileNotFoundError -- the feature is absent);
GREEN once the dashboard bundle lands and is complete.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
BI_DIR = REPO_ROOT / "bi"
CHARTS_DIR = BI_DIR / "charts"
DATASETS_DIR = BI_DIR / "datasets" / "main"
README = BI_DIR / "README.md"
DASHBOARD_YAML = BI_DIR / "dashboards" / "adventure_works_sales.yaml"

# FR-7's required dashboard-wide filter set: label -> the column name that must be targeted by a
# native filter, sourced from one of the committed bi/ datasets (question_a_sales_detail /
# question_a_sales_by_reason carry the full required-filter column set, P4-02).
REQUIRED_FILTERS = {
    "sales channel": "is_online",
    "product": "product_name",
    "card type": "card_type",
    "sales reason": "sales_reason_name",
    "order date": "date_day",
    "customer": "customer_name",
    "order status": "status_label",
    "city": "city",
    "state": "state_province",
    "country": "country",
}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(
            f"{rel} does not exist -- the P4-08 dashboard bundle isn't built yet"
        )
    return yaml.safe_load(path.read_text())


def all_chart_yamls() -> dict[str, dict]:
    """Every currently-committed chart, keyed by its uuid -- the dashboard must reference all."""
    charts: dict[str, dict] = {}
    for path in sorted(CHARTS_DIR.glob("*.yaml")):
        chart = load_yaml(path)
        charts[chart["uuid"]] = chart
    return charts


def all_dataset_yamls() -> dict[str, dict]:
    datasets: dict[str, dict] = {}
    for path in sorted(DATASETS_DIR.glob("*.yaml")):
        dataset = load_yaml(path)
        datasets[dataset["uuid"]] = dataset
    return datasets


def collect_position_chart_uuids(node) -> set[str]:
    """Walk the dashboard's ``position`` tree, collecting every CHART node's referenced uuid."""
    found: set[str] = set()
    if isinstance(node, dict):
        if node.get("type") == "CHART":
            meta = node.get("meta") or {}
            chart_uuid = meta.get("uuid")
            if chart_uuid:
                found.add(chart_uuid)
        for value in node.values():
            found |= collect_position_chart_uuids(value)
    elif isinstance(node, list):
        for item in node:
            found |= collect_position_chart_uuids(item)
    return found


def main() -> int:
    failures: list[str] = []

    dashboard = load_yaml(DASHBOARD_YAML)
    charts = all_chart_yamls()
    datasets = all_dataset_yamls()

    # --- 1. every currently-committed chart is referenced on the dashboard --------------------
    position = dashboard.get("position") or {}
    referenced_uuids = collect_position_chart_uuids(position)
    missing_charts = {
        chart["slice_name"]: chart_uuid
        for chart_uuid, chart in charts.items()
        if chart_uuid not in referenced_uuids
    }
    if missing_charts:
        failures.append(f"charts missing from dashboard position: {missing_charts}")
    else:
        print(f"[OK] all {len(charts)} committed charts are referenced on the dashboard")

    unknown_uuids = referenced_uuids - set(charts)
    if unknown_uuids:
        failures.append(
            f"dashboard references chart uuid(s) with no matching bi/charts/*.yaml: {unknown_uuids}"
        )

    # --- 2. dashboard-wide FR-7 filter set, each targeting a real filterable column -----------
    metadata = dashboard.get("metadata") or {}
    native_filters = metadata.get("native_filter_configuration") or []

    targeted_columns: set[str] = set()
    for nf in native_filters:
        for target in nf.get("targets", []):
            dataset_uuid = target.get("datasetUuid")
            column = (target.get("column") or {}).get("name")
            if not column:
                continue
            if dataset_uuid not in datasets:
                failures.append(
                    f"native filter {nf.get('name')!r} targets unknown dataset "
                    f"uuid {dataset_uuid!r}"
                )
                continue
            dataset_columns = {
                c["column_name"]: c for c in datasets[dataset_uuid].get("columns", [])
            }
            col_def = dataset_columns.get(column)
            if col_def is None:
                failures.append(
                    f"native filter {nf.get('name')!r} targets column {column!r}, not present on "
                    f"dataset {datasets[dataset_uuid]['table_name']!r}"
                )
                continue
            if not col_def.get("filterable", False):
                failures.append(
                    f"native filter {nf.get('name')!r} targets column {column!r} on "
                    f"{datasets[dataset_uuid]['table_name']!r}, which is not filterable"
                )
                continue
            targeted_columns.add(column)

    for label, column in REQUIRED_FILTERS.items():
        status = "OK" if column in targeted_columns else "MISSING"
        print(f"[{status}] required filter '{label}' -> column {column!r} wired dashboard-wide")
        if column not in targeted_columns:
            failures.append(f"required filter '{label}' ({column}) not wired on the dashboard")

    # --- 3. every metric used by any dataset the dashboard's charts read is documented --------
    used_dataset_uuids: set[str] = {
        chart["dataset_uuid"] for chart in charts.values() if chart.get("dataset_uuid")
    }

    used_metric_names: set[str] = set()
    for dataset_uuid in used_dataset_uuids:
        dataset = datasets.get(dataset_uuid)
        if dataset is None:
            failures.append(f"chart references unknown dataset uuid {dataset_uuid!r}")
            continue
        for metric in dataset.get("metrics", []):
            used_metric_names.add(metric["metric_name"])

    readme_text = README.read_text()
    undocumented = sorted(name for name in used_metric_names if f"`{name}`" not in readme_text)
    if undocumented:
        failures.append(
            f"metrics used on the dashboard but undocumented in bi/README.md: {undocumented}"
        )
    else:
        print(
            f"[OK] all {len(used_metric_names)} distinct metrics used on the dashboard's charts "
            "are documented in bi/README.md"
        )

    # --- 4. run instructions for this dashboard exist in bi/README.md -------------------------
    if "dashboards/adventure_works_sales.yaml" not in readme_text:
        failures.append("bi/README.md does not mention the dashboard bundle / its run instructions")
    else:
        print("[OK] bi/README.md documents the dashboard bundle")

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) did not pass:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        "\nPASSED: the dashboard bundle references every committed chart, wires every FR-7 "
        "dashboard-wide filter to a real filterable column, and every metric it uses is "
        "documented in bi/README.md."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
