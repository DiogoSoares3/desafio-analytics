"""Outer behaviour test (P4-07) -- question-f chart + Promotion-impact hero KPI reconcile.

Realizes the P4-07 Gherkin scenario (docs/phases/phase-4/backlog.md): the question-f chart (top
product by units purchased for the "Promotion" sales reason -- CHALLENGE.md question f) and the
fifth hero KPI tile (Promotion-impact, FR-8) must each compute the *exact same* number as a direct
aggregate query written independently against ``fct_sales`` joined through
``bridge_order_sales_reason`` to ``dim_sales_reason`` (ADR-0003 -- the base fact carries no reason
FK, so this join does not fan out gross for a single-reason filter, per the invariant P3-04's
singular test already proves). No dbt test exists for Phase 4, so this reconciliation check is the
outer test itself (ARCHITECTURE.md SS BI), same seam/mechanism as P4-01's
``scripts/validate_hero_kpis.py``.

Filter value: per PROGRESS.md's resolved tactical note, the real reason row is named
``sales_reason_name = 'On Promotion'`` (``sales_reason_type = 'Promotion'`` also matches) -- the
bare string ``'Promotion'`` matches zero rows in ``dim_sales_reason`` and was a bug fixed in P3-04
(PR #22). This test uses the real, non-vacuous filter.

Usage
-----
    uv run python scripts/validate_question_f.py

Exits non-zero (and prints what mismatched or which file is missing) on failure -- this is a test,
not a report. RED before ``bi/datasets/main/vw_promotion_reason_sales.yaml`` and
``bi/charts/question_f_top_product_promotion.yaml`` / ``bi/charts/hero_promotion_impact.yaml`` exist
(FileNotFoundError -- the feature is absent); GREEN once those are built and their declared SQL
agrees with the direct join.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"

DATASET_YAML = BI_DIR / "datasets" / "main" / "vw_promotion_reason_sales.yaml"
QUESTION_F_CHART_YAML = BI_DIR / "charts" / "question_f_top_product_promotion.yaml"
HERO_PROMOTION_IMPACT_CHART_YAML = BI_DIR / "charts" / "hero_promotion_impact.yaml"

# The real reason-row value (PROGRESS.md "Open questions" / P3-04 PR #22 fix) -- 'Promotion' alone
# matches zero rows in dim_sales_reason.
PROMOTION_REASON_NAME = "On Promotion"

# Direct join, written independently of the bi/ YAML -- the reconciliation oracle the Gherkin
# scenario asserts against (docs/phases/phase-4/backlog.md P4-07). Joins fct_sales ->
# sales_order_number -> bridge_order_sales_reason -> dim_sales_reason, filtered to the Promotion
# reason, grouped by product (via dim_product for the human-readable name) -- no fan-out per
# ADR-0003 / P3-04.
DIRECT_TOP_PRODUCT_SQL = f"""
    select
        dim_product.product_name,
        sum(fct_sales.order_qty) as units
    from fct_sales
    inner join bridge_order_sales_reason
        on fct_sales.sales_order_number = bridge_order_sales_reason.sales_order_number
    inner join dim_sales_reason
        on bridge_order_sales_reason.sales_reason_key = dim_sales_reason.sales_reason_key
    inner join dim_product
        on fct_sales.product_key = dim_product.product_key
    where dim_sales_reason.sales_reason_name = '{PROMOTION_REASON_NAME}'
    group by dim_product.product_name
    order by units desc
    limit 1
"""

# Promotion-impact hero KPI: total gross revenue attributable to Promotion-reason orders (not
# discount_amount -- the EDA notebook, P4-09, found discount_amount sits entirely on the
# reseller/store channel while the "On Promotion" reason tag is exclusively on online orders, so
# sum(discount_amount) over this join is structurally zero; sum(gross_revenue) is the meaningful,
# non-degenerate "impact" figure and is documented as such in bi/README.md).
DIRECT_PROMOTION_IMPACT_SQL = f"""
    select sum(fct_sales.gross_revenue)
    from fct_sales
    inner join bridge_order_sales_reason
        on fct_sales.sales_order_number = bridge_order_sales_reason.sales_order_number
    inner join dim_sales_reason
        on bridge_order_sales_reason.sales_reason_key = dim_sales_reason.sales_reason_key
    where dim_sales_reason.sales_reason_name = '{PROMOTION_REASON_NAME}'
"""


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(
            f"{rel} does not exist -- P4-07's bi/ assets have not been built yet"
        )
    return yaml.safe_load(path.read_text())


def dataset_sql(dataset: dict) -> str:
    sql = dataset.get("sql")
    if not sql:
        raise KeyError(f"{DATASET_YAML.name} does not declare a virtual dataset 'sql'")
    return sql


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


def chart_reason_filter(chart: dict) -> str:
    """Pull the sales_reason_name adhoc filter value declared on a chart."""
    params = chart.get("params", {})
    for flt in params.get("adhoc_filters", []):
        if flt.get("subject") == "sales_reason_name":
            return flt["comparator"]
    raise KeyError("no sales_reason_name adhoc_filter declared on chart params")


def main() -> int:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    failures: list[str] = []

    # --- Question-f: top product by units, Promotion reason filter -------------------------
    dataset = load_yaml(DATASET_YAML)
    view_sql = dataset_sql(dataset)

    chart = load_yaml(QUESTION_F_CHART_YAML)
    reason_filter = chart_reason_filter(chart)
    if reason_filter != PROMOTION_REASON_NAME:
        failures.append(
            f"question-f chart filters sales_reason_name = {reason_filter!r}, expected "
            f"{PROMOTION_REASON_NAME!r}"
        )

    metric_name = chart_metric_name(chart)
    metric_sql = dataset_metric_sql(dataset, metric_name)

    exported_row = con.execute(
        f"""
        with vw as ({view_sql})
        select product_name, {metric_sql} as units
        from vw
        where sales_reason_name = '{reason_filter}'
        group by product_name
        order by units desc
        limit 1
        """
    ).fetchone()
    direct_row = con.execute(DIRECT_TOP_PRODUCT_SQL).fetchone()
    assert exported_row is not None and direct_row is not None

    match_product = exported_row[0] == direct_row[0]
    match_units = round(float(exported_row[1]), 2) == round(float(direct_row[1]), 2)
    status = "OK" if (match_product and match_units) else "MISMATCH"
    print(
        f"[{status}] Question f (top product, Promotion reason): exported = "
        f"{exported_row!r} | direct join = {direct_row!r}"
    )
    if not (match_product and match_units):
        failures.append("question-f top product / units")

    # --- Hero KPI: Promotion-impact --------------------------------------------------------
    hero_chart = load_yaml(HERO_PROMOTION_IMPACT_CHART_YAML)
    hero_metric_name = chart_metric_name(hero_chart)
    hero_reason_filter = chart_reason_filter(hero_chart)
    if hero_reason_filter != PROMOTION_REASON_NAME:
        failures.append(
            f"hero_promotion_impact chart filters sales_reason_name = {hero_reason_filter!r}, "
            f"expected {PROMOTION_REASON_NAME!r}"
        )
    hero_metric_sql = dataset_metric_sql(dataset, hero_metric_name)

    exported_impact_row = con.execute(
        f"""
        with vw as ({view_sql})
        select {hero_metric_sql}
        from vw
        where sales_reason_name = '{hero_reason_filter}'
        """
    ).fetchone()
    direct_impact_row = con.execute(DIRECT_PROMOTION_IMPACT_SQL).fetchone()
    assert exported_impact_row is not None and direct_impact_row is not None
    exported_impact = exported_impact_row[0]
    direct_impact = direct_impact_row[0]

    match_impact = round(float(exported_impact), 2) == round(float(direct_impact), 2)
    status = "OK" if match_impact else "MISMATCH"
    print(
        f"[{status}] Promotion-impact hero KPI: exported metric ({hero_metric_name!r}) = "
        f"{exported_impact!r} | direct join aggregate = {direct_impact!r}"
    )
    if not match_impact:
        failures.append("Promotion-impact hero KPI")

    con.close()

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) did not reconcile: {failures}", file=sys.stderr)
        return 1

    print(
        "\nPASSED: question-f chart and the Promotion-impact hero KPI reconcile to a direct join."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
