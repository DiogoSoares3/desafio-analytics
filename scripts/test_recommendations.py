"""Outer behaviour test (P4-10) -- commercial recommendations doc realizes the Gherkin scenario.

Realizes docs/phases/phase-4/backlog.md's P4-10 scenario: ``docs/recommendations.md`` must exist,
contain a prioritized list of concrete, actionable recommendations, and every recommendation must
cite at least one specific number that traces back to the finished dashboard (P4-08) or the EDA
notebook (P4-09) -- not invented figures. At least one recommendation must directly address
Silvana Teixeira's stated skepticism (promotions vs. data-driven decisions) using the question-f /
Promotion-impact figures.

This is a pure documentation artifact with no dbt/BI schema seam (ARCHITECTURE.md SS BI --
"manual/external" per the phase PRD), so its acceptance scenario is realized as an outer check
script, same pattern as the other ``scripts/validate_*``/``test_*`` outer tests. The gate here is
NOT "does the doc exist" alone -- it independently recomputes every grounded figure directly from
the built ``fct_sales``/``dim_*``/``bridge_order_sales_reason`` marts (no dependency on bi/README's
prose, which could itself drift) and then parses/greps the doc's recommendation text for numeric
citations, checking each against that independently-computed oracle within a tolerance that
accounts for common formatting (``$6.36M``, ``86%``, ``~20x``, ``3,515``, ...).

Usage
-----
    uv run python scripts/test_recommendations.py

Exits non-zero (reason printed) on failure. RED before ``docs/recommendations.md`` exists
(FileNotFoundError -- the feature is absent); GREEN once the doc is written and its recommendations
are prioritized, cite real figures, and cover the Promotion-skepticism angle.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

REPO_ROOT = Path(__file__).resolve().parents[1]
DUCKDB_PATH = REPO_ROOT / "data" / "adventureworks.duckdb"
DOC_PATH = REPO_ROOT / "docs" / "recommendations.md"

MIN_RECOMMENDATIONS = 3

# --------------------------------------------------------------------------------------------
# Independent oracle: recompute every grounded figure directly from the built marts (not read
# from bi/README.md or the notebook's rendered output, which could itself have drifted).
# --------------------------------------------------------------------------------------------


def fetchone_checked(relation: duckdb.DuckDBPyRelation) -> tuple:
    row = relation.fetchone()
    assert row is not None, "expected exactly one row, got none"
    return row


def compute_grounded_figures(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    revenue, orders, units = fetchone_checked(
        con.sql(
            "select sum(gross_revenue), count(distinct sales_order_number), sum(order_qty) "
            "from fct_sales"
        )
    )
    aov = fetchone_checked(
        con.sql(
            "select (sum(gross_revenue) - sum(discount_amount)) "
            "/ count(distinct sales_order_number) from fct_sales"
        )
    )[0]

    category_mix = con.sql(
        """
        select p.category_name, sum(f.gross_revenue) as rev, sum(f.order_qty) as units
        from fct_sales as f
        inner join dim_product as p using (product_key)
        group by 1
        order by 2 desc
        """
    ).fetchall()
    bikes_rev = next(r for c, r, u in category_mix if c == "Bikes")
    bikes_units = next(u for c, r, u in category_mix if c == "Bikes")

    channel_mix = con.sql(
        """
        select is_online, count(distinct sales_order_number) as orders,
               sum(gross_revenue) as rev,
               sum(gross_revenue) / count(distinct sales_order_number) as aov
        from fct_sales
        group by 1
        """
    ).fetchall()
    reseller_orders, reseller_rev, reseller_aov = next(
        (o, r, a) for online, o, r, a in channel_mix if not online
    )
    online_orders, online_rev, online_aov = next(
        (o, r, a) for online, o, r, a in channel_mix if online
    )

    geo = con.sql(
        """
        select g.country, sum(f.gross_revenue) as rev
        from fct_sales as f
        inner join dim_geography as g using (geography_key)
        group by 1
        order by 2 desc
        """
    ).fetchall()
    us_rev = next(r for country, r in geo if country == "United States")
    ca_rev = next(r for country, r in geo if country == "Canada")

    promo_orders, promo_gross = fetchone_checked(
        con.sql(
            """
            select count(distinct b.sales_order_number), sum(f.gross_revenue)
            from fct_sales as f
            inner join bridge_order_sales_reason as b using (sales_order_number)
            inner join dim_sales_reason as r using (sales_reason_key)
            where r.sales_reason_type = 'Promotion'
            """
        )
    )

    discount_total = fetchone_checked(con.sql("select sum(discount_amount) from fct_sales"))[0]
    discount_by_channel = con.sql(
        "select is_online, sum(discount_amount) from fct_sales group by 1"
    ).fetchall()
    online_discount = next(d for online, d in discount_by_channel if online)
    reseller_discount = next(d for online, d in discount_by_channel if not online)

    top_promo_product = fetchone_checked(
        con.sql(
            """
            select p.product_name, sum(f.order_qty) as units
            from fct_sales as f
            inner join bridge_order_sales_reason as b using (sales_order_number)
            inner join dim_sales_reason as r using (sales_reason_key)
            inner join dim_product as p using (product_key)
            where r.sales_reason_name = 'On Promotion'
            group by 1
            order by 2 desc
            limit 1
            """
        )
    )

    top_customer = fetchone_checked(
        con.sql(
            """
            select c.full_name, sum(f.gross_revenue) as rev
            from fct_sales as f
            inner join dim_customer as c using (customer_key)
            group by 1
            order by 2 desc
            limit 1
            """
        )
    )

    top_city = fetchone_checked(
        con.sql(
            """
            select g.city, sum(f.gross_revenue) as rev
            from fct_sales as f
            inner join dim_geography as g using (geography_key)
            group by 1
            order by 2 desc
            limit 1
            """
        )
    )

    return {
        "total_revenue": float(revenue),
        "orders": float(orders),
        "units": float(units),
        "aov": float(aov),
        "bikes_revenue": float(bikes_rev),
        "bikes_revenue_pct": float(bikes_rev) / float(revenue) * 100,
        "bikes_units": float(bikes_units),
        "bikes_units_pct": float(bikes_units) / float(units) * 100,
        "reseller_orders": float(reseller_orders),
        "reseller_orders_pct": float(reseller_orders) / float(orders) * 100,
        "reseller_revenue": float(reseller_rev),
        "reseller_revenue_pct": float(reseller_rev) / float(revenue) * 100,
        "reseller_aov": float(reseller_aov),
        "online_orders": float(online_orders),
        "online_revenue": float(online_rev),
        "online_aov": float(online_aov),
        "aov_gap_multiplier": float(reseller_aov) / float(online_aov),
        "us_revenue": float(us_rev),
        "us_revenue_pct": float(us_rev) / float(revenue) * 100,
        "canada_revenue": float(ca_rev),
        "promo_orders": float(promo_orders),
        "promo_gross": float(promo_gross),
        "promo_gross_pct": float(promo_gross) / float(revenue) * 100,
        "discount_total": float(discount_total),
        "online_discount": float(online_discount),
        "reseller_discount": float(reseller_discount),
        "top_promo_product_units": float(top_promo_product[1]),
        "top_customer_revenue": float(top_customer[1]),
        "top_city_revenue": float(top_city[1]),
        # Régua headline reconciliation figure (2011 all-channel gross, ADR-0001) -- a trust
        # anchor worth citing to the CEO/Silvana, independent of the fct_sales full-history sums.
        "reconciliation_2011": 12646112.16,
    }


# Figures that specifically evidence the Promotion-vs-data-driven skepticism angle (question f /
# hero Promotion-Impact KPI + the discount-by-channel nuance P4-09's EDA found).
PROMOTION_KEYS = {"promo_orders", "promo_gross", "discount_total", "online_discount"}

# --------------------------------------------------------------------------------------------
# Doc parsing: pull out numbered recommendation blocks and the numeric tokens each one cites.
# --------------------------------------------------------------------------------------------

RECOMMENDATION_HEADING_RE = re.compile(r"^#{2,4}\s*(\d+)[.).]\s*(.+)$", re.MULTILINE)

DOLLAR_RE = re.compile(r"\$\s?[\d][\d,]*(?:\.\d+)?\s?[MKmk]?\b")
PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s?%")
MULTIPLIER_RE = re.compile(r"\b\d+(?:\.\d+)?\s?[xX]\b")
PLAIN_NUMBER_RE = re.compile(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b")


def parse_recommendations(text: str) -> list[tuple[int, str, str]]:
    """Return ``[(priority, title, body), ...]`` for each ``### N. Title`` block in the doc."""
    matches = list(RECOMMENDATION_HEADING_RE.finditer(text))
    blocks = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        priority = int(m.group(1))
        title = m.group(2).strip()
        body = text[start:end].strip()
        blocks.append((priority, title, body))
    return blocks


def normalize_token(token: str) -> tuple[str, float] | None:
    t = token.strip()
    if t.endswith("%"):
        try:
            return ("percent", float(t[:-1].strip()))
        except ValueError:
            return None
    if t[-1] in "xX" and any(c.isdigit() for c in t):
        try:
            return ("multiplier", float(t[:-1].strip()))
        except ValueError:
            return None
    if t.startswith("$"):
        body = t[1:].strip()
        multiplier = 1.0
        if body and body[-1] in "Mm":
            multiplier = 1_000_000.0
            body = body[:-1]
        elif body and body[-1] in "Kk":
            multiplier = 1_000.0
            body = body[:-1]
        try:
            return ("numeric", float(body.replace(",", "")) * multiplier)
        except ValueError:
            return None
    try:
        return ("numeric", float(t.replace(",", "")))
    except ValueError:
        return None


def extract_numeric_citations(text: str) -> list[tuple[str, float]]:
    tokens = (
        DOLLAR_RE.findall(text)
        + PERCENT_RE.findall(text)
        + MULTIPLIER_RE.findall(text)
        + PLAIN_NUMBER_RE.findall(text)
    )
    citations = []
    for tok in tokens:
        norm = normalize_token(tok)
        if norm is not None:
            citations.append(norm)
    return citations


def citation_matches_any(kind: str, value: float, grounded: dict[str, float]) -> list[str]:
    """Return the grounded-figure keys this citation reconciles to (within tolerance)."""
    hits = []
    for key, gvalue in grounded.items():
        if kind == "percent":
            if not key.endswith("_pct"):
                continue
            if abs(value - gvalue) <= 3.0:
                hits.append(key)
        elif kind == "multiplier":
            if key != "aov_gap_multiplier":
                continue
            if abs(value - gvalue) <= 3.0:
                hits.append(key)
        else:  # "numeric" -- money or plain count
            if key.endswith("_pct"):
                continue
            tol = max(1.0, gvalue * 0.02)
            if abs(value - gvalue) <= tol:
                hits.append(key)
    return hits


def main() -> int:
    if not DOC_PATH.exists():
        raise FileNotFoundError(
            f"{DOC_PATH.relative_to(REPO_ROOT)} does not exist -- P4-10's recommendations doc "
            "has not been written yet"
        )

    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    grounded = compute_grounded_figures(con)
    con.close()

    text = DOC_PATH.read_text()
    failures: list[str] = []

    if "Silvana" not in text:
        failures.append("doc never mentions Silvana by name -- not explicitly framed for her")

    blocks = parse_recommendations(text)
    print(f"Found {len(blocks)} numbered recommendation(s).")
    if len(blocks) < MIN_RECOMMENDATIONS:
        failures.append(
            f"only {len(blocks)} numbered recommendations found, need >= {MIN_RECOMMENDATIONS}"
        )

    priorities = [p for p, _, _ in blocks]
    if priorities != sorted(priorities) or priorities != list(range(1, len(priorities) + 1)):
        failures.append(f"recommendations are not a clean 1..N priority sequence: {priorities}")

    promotion_recommendation_found = False

    for priority, title, body in blocks:
        full_text = f"{title}\n{body}"
        citations = extract_numeric_citations(full_text)

        matched_keys: set[str] = set()
        for kind, value in citations:
            matched_keys.update(citation_matches_any(kind, value, grounded))

        status = "OK" if matched_keys else "NO GROUNDED CITATION"
        print(f"  [{status}] #{priority} {title!r} -- reconciled to: {sorted(matched_keys)}")

        if not matched_keys:
            failures.append(
                f"recommendation #{priority} {title!r} cites no number that reconciles to a "
                "grounded dashboard/EDA figure"
            )

        mentions_promotion = "promotion" in full_text.lower()
        if mentions_promotion and matched_keys & PROMOTION_KEYS:
            promotion_recommendation_found = True

    if not promotion_recommendation_found:
        failures.append(
            "no recommendation both mentions 'promotion' and cites a Promotion-impact/question-f "
            "figure (promo_orders, promo_gross, discount_total, online_discount) -- Silvana's "
            "promotion-vs-data-driven skepticism is not directly addressed"
        )

    if failures:
        print(f"\nFAILED: {len(failures)} check(s):", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1

    print(
        f"\nPASSED: {len(blocks)} prioritized recommendations, each citing a grounded figure; "
        "the Promotion-vs-data-driven skepticism is directly addressed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
