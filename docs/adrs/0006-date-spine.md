# ADR-0006: dim_date via dynamic-range date_spine

> Status: accepted · Date: 2026-07-10 · Deciders: engineer (via /grill-me)
> Raised during ARCHITECTURE authoring — PRD open question #3: the calendar range for `dim_date`.

## Context
Question e (orders/quantity/value time series by month & year) and every date filter depend on a
gap-free calendar dimension. Hardcoding a range risks missing dates if the data slice changes.

## Decision
Generate **`dim_date`** with **`dbt_utils.date_spine`**, bounds computed **dynamically** from
`min(order_date)` to `max(order_date)` in the staged sales data (AdventureWorks online orders run
≈ 2011–2014, but the range is computed, not hardcoded). Grain: one row per calendar day. Attributes:
year, quarter, month number, month name, year-month, day, day-of-week, weekday/weekend flag.
Materialized as a **table**. `fct_sales` joins on `order_date`.

## Discarded alternatives
| Considered | Rejected because |
|---|---|
| Hardcoded 2011–2014 range | Breaks if the data slice differs; less reproducible for a grader. |
| Materialize as view | Recomputed on every query; table is cheap and stable for a snapshot. |

## Consequences
Complete, gap-free time axis for the time-series question and all date filters; reproducible across data
slices. Updates `ARCHITECTURE.md` (components: `dim_date`). Depends on the `dbt_utils` package.
