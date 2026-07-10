# ADR-0007: Hashed surrogate keys as dimension PKs

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — the challenge requires PK tests on every dim and fact (step 5.iii).

## Context
Challenge step 5.iii requires "tests on primary keys for dimension and fact tables." Every dim and the
fact need a clean single-column PK that `unique` + `not_null` tests can guard, and the fact needs
unambiguous FKs into each dimension for relationship tests.

## Decision
Generate surrogate keys with **`dbt_utils.generate_surrogate_key`** (a hash) as each dimension's PK:
`product_key`, `customer_key`, `date_key`, `geography_key`, `credit_card_key`, `sales_reason_key`,
`order_status_key`. **`fct_sales`** carries these seven surrogate keys as FKs, **plus degenerate
dimensions** on the fact itself — `sales_order_number` and the order-line number (natural identifiers,
no dimension table). The fact PK is the surrogate of `SalesOrderDetailID`.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Natural/business keys as PKs | Composite or reused across schemas; messier PK/relationship tests. |
| Integer identity SKs | Non-deterministic across runs; hash SKs are reproducible offline (régua). |

## Consequences
PK tests become trivial (`unique` + `not_null` on each `_key`); fact→dim relationship tests are clean —
both directly satisfy the challenge's PK/data-quality requirements. Hash SKs are deterministic and
reproducible (supports NFR-1). Degenerate dimensions keep order/line identity on the fact without extra
tables. Depends on `dbt_utils`. Updates `ARCHITECTURE.md` (key strategy).
