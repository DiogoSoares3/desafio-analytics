# ADR-0004: Sales fact grain — one row per sales-order line

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — PRD open question #2: line vs header grain for `fct_sales`.

## Context
`SalesOrderDetail` is one row per product line; `SalesOrderHeader` is one row per order. ADR-0001 defines
gross as `UnitPrice × OrderQty` at line level. Questions a/b/f need product-level slicing (line grain),
while question e and "number of orders" need order-level counts, and freight/tax live on the header.

## Decision
Build **`fct_sales` at the sales-order-line grain** — one row per `SalesOrderDetailID`. Header-level
metrics are **derived**: order count = `count(distinct sales_order_id)`; freight/tax carried as
header-level attributes (not summed at line grain). Gross revenue sums trivially to the audit figure at
this grain.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Header grain (one row per order) | Cannot slice by product / discount / promotion; breaks questions a, b, f. |
| Two facts (line + header) | Extra surface and reconciliation burden; line grain + derived measures covers all questions. |

## Consequences
Finest grain the business questions require; gross reconciliation (ADR-0001) is a direct line-level sum.
"Number of orders" is a distinct-count measure, not a row count — documented so consumers don't sum row
counts. Freight/tax are order-level and must not be averaged across lines. Fixes the grain that every
dimension FK and the sales-reason bridge (ADR-0003) attach to. Updates `ARCHITECTURE.md` (components: `fct_sales`).
