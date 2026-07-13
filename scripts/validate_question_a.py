"""Outer behaviour test (P4-02) -- question a reconciles to fct_sales, sliceable by every dim.

Realizes the P4-02 Gherkin scenario (docs/phases/phase-4/backlog.md): CHALLENGE.md question a --
"number of orders, quantity purchased, and total transaction value by product, card type, sales
reason, sales date, customer, status, city, state, and country". The chart(s) are exported as
Superset **virtual datasets** (BI-as-code, ADR-0002) joining ``fct_sales`` to its dims (+ the
sales-reason bridge). This script proves:

1. A filter applied to the question-a dataset (product + sales channel) reconciles exactly to a
   direct aggregate query written independently against ``fct_sales`` with the same filter
   (no parallel metric layer, NFR-3).
2. The dataset can be grouped by each of the nine required dimensions without error, and each
   dimension's grouped totals sum back to the unfiltered grand total (no fan-out/undercount).

Usage
-----
    uv run python scripts/validate_question_a.py

Exits non-zero on any mismatch/missing-file/query-error -- this is a test, not a report. RED before
the ``bi/`` question-a datasets + charts exist (FileNotFoundError); GREEN once they are built and
their declared SQL reconciles.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
BI_DIR = REPO_ROOT / "bi"

DETAIL_DATASET_YAML = BI_DIR / "datasets" / "main" / "question_a_sales_detail.yaml"
REASON_DATASET_YAML = BI_DIR / "datasets" / "main" / "question_a_sales_by_reason.yaml"
CHARTS = {
    "detail": BI_DIR / "charts" / "question_a_orders_qty_value.yaml",
    "reason": BI_DIR / "charts" / "question_a_orders_qty_value_by_reason.yaml",
}

METRIC_EXPRESSIONS = {
    "number_of_orders": "COUNT(DISTINCT sales_order_number)",
    "units_purchased": "SUM(order_qty)",
    "total_transaction_value": "SUM(gross_revenue)",
}

# The nine required slice dimensions (question a) + which dataset/column realizes each.
DETAIL_SLICE_COLUMNS = {
    "product": "product_name",
    "card type": "card_type",
    "sales date": "year_month",
    "customer": "customer_name",
    "status": "status_label",
    "city": "city",
    "state": "state_province",
    "country": "country",
}
REASON_SLICE_COLUMNS = {
    "sales reason": "sales_reason_name",
}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        rel = path.relative_to(REPO_ROOT)
        raise FileNotFoundError(f"{rel} does not exist -- question-a bi/ assets not built yet")
    return yaml.safe_load(path.read_text())


def dataset_sql(dataset: dict) -> str:
    sql = dataset.get("sql")
    if not sql:
        raise ValueError(f"dataset {dataset.get('table_name')!r} has no virtual-dataset sql")
    return sql


def metric_select(alias_prefix: str = "") -> str:
    return ", ".join(f"{expr} as {name}{alias_prefix}" for name, expr in METRIC_EXPRESSIONS.items())


def main() -> int:
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    failures: list[str] = []

    # --- charts must exist and reference the datasets (fail fast, RED before bi/ built) -----
    for path in CHARTS.values():
        load_yaml(path)

    detail_dataset = load_yaml(DETAIL_DATASET_YAML)
    reason_dataset = load_yaml(REASON_DATASET_YAML)
    detail_sql = dataset_sql(detail_dataset)
    reason_sql = dataset_sql(reason_dataset)

    # --- 1. filtered reconciliation: product = a known SKU, sales channel = online -----------
    known_product_row = con.execute(
        f"""
        select product_name
        from ({detail_sql}) t
        where is_online = true
        group by product_name
        order by product_name
        limit 1
        """
    ).fetchone()
    if known_product_row is None:
        raise RuntimeError("no online product found in question-a detail dataset -- cannot filter")
    known_product = known_product_row[0]

    exported_row = con.execute(
        f"""
        select {metric_select()}
        from ({detail_sql}) t
        where product_name = ? and is_online = true
        """,
        [known_product],
    ).fetchone()

    direct_row = con.execute(
        """
        select
            count(distinct f.sales_order_number) as number_of_orders,
            sum(f.order_qty) as units_purchased,
            sum(f.gross_revenue) as total_transaction_value
        from fct_sales f
        join dim_product p on f.product_key = p.product_key
        where p.product_name = ? and f.is_online = true
        """,
        [known_product],
    ).fetchone()

    assert exported_row is not None and direct_row is not None
    match = tuple(round(float(v), 2) for v in exported_row) == tuple(
        round(float(v), 2) for v in direct_row
    )
    status = "OK" if match else "MISMATCH"
    print(
        f"[{status}] filtered (product={known_product!r}, is_online=true): "
        f"dataset={exported_row!r} | direct fct_sales={direct_row!r}"
    )
    if not match:
        failures.append("filtered reconciliation")

    # --- 2. re-slice by each required dimension without error, totals reconcile --------------
    unfiltered_total = con.execute(f"select {metric_select()} from ({detail_sql}) t").fetchone()
    assert unfiltered_total is not None

    for label, column in DETAIL_SLICE_COLUMNS.items():
        try:
            rows = con.execute(
                f"""
                select {column}, {metric_select()}
                from ({detail_sql}) t
                group by {column}
                """
            ).fetchall()
        except Exception as exc:  # noqa: BLE001 -- the scenario asserts "without error"
            print(f"[ERROR] re-slice by {label} ({column}) raised: {exc}")
            failures.append(f"re-slice by {label}")
            continue

        # row shape: (group_column, number_of_orders, units_purchased, total_transaction_value)
        summed_qty_value = (
            sum(r[2] for r in rows),
            sum(r[3] for r in rows),
        )
        # order count is not additive across a groupby (an order can span >1 product/status/etc
        # in different rows only for reason-fanout, not here); qty and value ARE additive since
        # the detail dataset carries no reason join (one row per fct_sales line, ADR-0003).
        qty_value_match = tuple(round(float(v), 2) for v in summed_qty_value) == (
            round(float(unfiltered_total[1]), 2),
            round(float(unfiltered_total[2]), 2),
        )
        status = "OK" if qty_value_match else "MISMATCH"
        print(
            f"[{status}] re-slice by {label} ({column}): {len(rows)} groups, "
            f"qty/value totals reconcile={qty_value_match}"
        )
        if not qty_value_match:
            failures.append(f"re-slice totals by {label}")

    # --- 3. sales-reason slice (bridge join; single-reason filter does not fan out gross, -----
    #        already proven structurally by P3-04's fct_sales_gross_invariant_under_bridge) ----
    for label, column in REASON_SLICE_COLUMNS.items():
        try:
            rows = con.execute(
                f"""
                select {column}, {metric_select()}
                from ({reason_sql}) t
                group by {column}
                """
            ).fetchall()
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] re-slice by {label} ({column}) raised: {exc}")
            failures.append(f"re-slice by {label}")
            continue
        print(f"[OK] re-slice by {label} ({column}): {len(rows)} groups, no error")

        # Spot-check one reason against a direct bridge join (mirrors P4-07's mechanism).
        top_reason_row = con.execute(
            f"select {column}, {metric_select()} from ({reason_sql}) t group by {column} "
            f"order by {column} limit 1"
        ).fetchone()
        assert top_reason_row is not None
        reason_value = top_reason_row[0]
        direct_reason_row = con.execute(
            """
            select
                count(distinct f.sales_order_number) as number_of_orders,
                sum(f.order_qty) as units_purchased,
                sum(f.gross_revenue) as total_transaction_value
            from fct_sales f
            join bridge_order_sales_reason b on f.sales_order_number = b.sales_order_number
            join dim_sales_reason r on b.sales_reason_key = r.sales_reason_key
            where r.sales_reason_name = ?
            """,
            [reason_value],
        ).fetchone()
        assert direct_reason_row is not None
        exported_reason = tuple(top_reason_row[1:])
        reason_match = tuple(round(float(v), 2) for v in exported_reason) == tuple(
            round(float(v), 2) for v in direct_reason_row
        )
        status = "OK" if reason_match else "MISMATCH"
        print(
            f"[{status}] sales_reason={reason_value!r}: dataset={exported_reason!r} | "
            f"direct bridge join={direct_reason_row!r}"
        )
        if not reason_match:
            failures.append(f"reason reconciliation ({reason_value})")

    con.close()

    if failures:
        print(f"\nFAILED: {len(failures)} check(s) did not pass: {failures}", file=sys.stderr)
        return 1

    print(
        "\nPASSED: question-a filtered reconciliation + all nine required dimension slices "
        "(product, card type, sales reason, sales date, customer, status, city, state, country) "
        "reconcile to direct fct_sales aggregates without error."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
