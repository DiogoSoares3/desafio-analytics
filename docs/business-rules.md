# Business Rules — AdventureWorks Analytics Engineering

> FR-12 deliverable. Consolidates the modeling decisions already ratified in `docs/adrs/` into one
> narrative reference — this document does not introduce new rules, it explains the ones the ADRs
> closed. See `docs/ARCHITECTURE.md` for the schema those rules produce.

## Scope: which sales are in the model
`fct_sales` includes **all sales channels — online and reseller — 2011 through 2014** ([ADR-0010](adrs/0010-sales-channel-scope.md)).
The project originally scoped to online-only, but the CEO's audited 2011 figure ($12,646,112.16) only
reconciles against **all** channels ($3.86M online + $8.78M reseller); the régua (reconciliation wins over
scope) settled it. Sales channel is not a partition — it is a filterable attribute (`is_online`) on every
fact row, so a dashboard consumer can still isolate online sales for a commercial view while the audit
test runs over the full, audited population.

## Gross, discount, and net revenue
Defined at **sales-order-line grain** ([ADR-0001](adrs/0001-gross-sales-definition-and-reconciliation.md), [ADR-0004](adrs/0004-sales-fact-grain-order-line.md)):

| Measure | Formula | Notes |
|---|---|---|
| `gross_revenue` | `UnitPrice × OrderQty` | Pre-discount, pre-tax, pre-freight — the audited basis. |
| `discount_amount` | `UnitPriceDiscount × UnitPrice × OrderQty` | |
| `net_revenue` | `gross_revenue − discount_amount` | Reconciles to source `LineTotal`. |

"Gross" deliberately excludes tax and freight (both are header-level, not summed at line grain) and is
pre-discount — discounts are tracked separately as a promotion-impact KPI, not netted into the headline
number. **2011 all-channel gross reconciles to exactly $12,646,112.16**, zero tolerance — this is the
project's trust anchor and is enforced by a dbt singular test on every build.

## Order counting and average order value
An order is **not** a fact row — a fact row is a line. **Order count = `count(distinct sales_order_number)`.**
Consumers who sum fact rows to count orders will over-count. **AOV = (gross − discount) ÷ distinct order
count** ([ADR-0004](adrs/0004-sales-fact-grain-order-line.md)).

## Sales reason is multi-valued — never fan out the fact
An order can carry more than one sales reason (`SalesOrderHeaderSalesReason`). Putting a reason key
directly on `fct_sales` would either lose reasons (single-reason FK) or duplicate line revenue on every
extra reason (fan-out fact). Instead: `dim_sales_reason` + `bridge_order_sales_reason` (grain: order ×
reason); **`fct_sales` carries no reason FK** ([ADR-0003](adrs/0003-sales-reason-multi-valued-bridge.md)).
Reason-filtered analysis (e.g. "which sales were On Promotion") joins `fct_sales → sales_order_number →
bridge → dim_sales_reason`. A **single**-reason filter is exact and does not double-count; summing gross
**across multiple** reasons for the same order will double-count and must be avoided by consumers. A
singular test asserts this invariant on every build.

## Geography is ship-to, not bill-to
An order can have different billing and shipping addresses. The commercial question ("where did revenue
go") is a shipping-market question, so `fct_sales`'s geography FK resolves to the **ship-to address**,
always present on an order. One conformed `dim_geography` (city + state/province + country) is reused by
both the fact and `dim_customer`'s home-geography attribute ([ADR-0005](adrs/0005-geography-conformance-ship-to.md)).
Bill-to analysis is out of scope for this version.

## Customers span both channels
`dim_customer` includes **both** individual (online, `Customer.PersonID`) and store/reseller
(`Customer.StoreID`) customers, distinguished by a `customer_type` attribute — a consequence of the
all-channel scope decision. Reseller lines have no credit card on file, so `dim_credit_card` carries an
explicit **"N/A" member** rather than leaving the fact's `credit_card_key` FK nullable
([ADR-0010](adrs/0010-sales-channel-scope.md)).

## No history tracking (SCD Type 1)
All seven dimensions overwrite on change (SCD Type 1) — one current row per entity, no
effective-dating. None of the business questions (a–f) need an attribute's value *as of the order date*;
adding Type 2 versioning would cost complexity with no analytical payoff at this scope
([ADR-0008](adrs/0008-scd-type-1.md)).

## Calendar coverage
`dim_date` spans the **actual** min→max order date found in the data (computed dynamically via
`dbt_utils.date_spine`), not a hardcoded range — so the model stays correct if the underlying data slice
changes ([ADR-0006](adrs/0006-date-spine.md)).

## Keys
Every dimension's primary key is a **deterministic hash** (`dbt_utils.generate_surrogate_key`) over its
natural key, not a natural key or an identity column — reproducible across rebuilds (the offline régua)
and trivial to PK-test (`unique` + `not_null`). `fct_sales`'s own primary key hashes
`SalesOrderDetailID`; `sales_order_number` and the order-line number ride along as degenerate dimensions
([ADR-0007](adrs/0007-surrogate-keys.md)).

## Layering (medallion via dbt)
Raw `adventure_works` source/seeds = **Bronze**. `staging/` (1:1 renamed/cast views) + `intermediate/`
(ephemeral joins and business-logic prep) = **Silver**. `dim_*` / `bridge_order_sales_reason` /
`fct_sales`, materialized as tables = **Gold**, the layer Superset reads
([ADR-0009](adrs/0009-medallion-via-dbt-layers.md)).

## BI numbers are the tested numbers
Superset connects directly to the same DuckDB marts dbt builds and tests — there is no second metric
layer (no DAX-equivalent). A dashboard figure is only ever as trustworthy as the reconciliation test
behind the mart it reads from ([ADR-0002](adrs/0002-bi-tool-apache-superset.md)).

## Full decision log
See `docs/adrs/0001`–`0010` for the complete context, discarded alternatives, and consequences behind
each rule above.
