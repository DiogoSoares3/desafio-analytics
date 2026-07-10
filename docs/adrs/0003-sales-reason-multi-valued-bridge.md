# ADR-0003: Sales reason modeled as a multi-valued bridge

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — PRD open question #1: an order has many sales reasons, but the
> fact is line-grain; hanging a single reason FK either loses data or double-counts revenue.

## Context
`SalesOrderHeaderSalesReason` is a bridge — one sales order can carry **multiple** sales reasons.
`fct_sales` is at order-line grain (ADR-0001 gross = `UnitPrice × OrderQty` at line level). Putting a
single `sales_reason_key` on the fact would lose reasons; fanning the fact out per reason would
**double-count gross revenue** and break the 2011 reconciliation. Question f only needs to *filter* units
by a reason ("Promotion"), not sum across reasons.

## Decision
Model **`dim_sales_reason`** (one row per reason) + **`bridge_order_sales_reason`** (grain: one row per
order × reason) — the Kimball multi-valued-dimension pattern. **`fct_sales` carries no reason FK**;
reason-filtered analysis joins `fct_sales → order_id → bridge_order_sales_reason → dim_sales_reason`.
A single-reason filter (e.g. "Promotion") is exact and does not double-count; summing *across* multiple
reasons can double-count and is documented as a caveat. A singular test asserts base-fact `sum(gross)` is
unchanged when the bridge is joined for a single-reason filter.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Single "primary reason" per order collapsed onto the fact | Arbitrary loss of information; orders legitimately have multiple reasons. |
| Fan `fct_sales` out to one row per line × reason | Double-counts gross revenue; breaks the 2011 reconciliation (ADR-0001). |
| Boolean reason flags (`is_promotion`, …) on the fact | Doesn't scale to all reasons; awkward for slicing; hides the dimension. |

## Consequences
Keeps `fct_sales` reconciliation-clean (no reason fan-out on the base grain). Reason analysis costs a
two-hop join through the bridge; consumers summing across reasons must dedupe (documented caveat).
Question f is answered exactly via a `Promotion`-filtered bridge join. Updates `ARCHITECTURE.md`
(components: `dim_sales_reason`, `bridge_order_sales_reason`; seams: singular test on gross invariance).
