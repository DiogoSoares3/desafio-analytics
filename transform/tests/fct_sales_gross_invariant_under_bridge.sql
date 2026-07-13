{{ config(severity='error') }}

{#-
    P3-04 / ADR-0003: fct_sales carries no reason FK; reason-filtered analysis joins through
    bridge_order_sales_reason (grain: order x reason). A single-reason filter (the "On Promotion"
    sales reason, sales_reason_type = 'Promotion' — CHALLENGE.md question f's "Promotion" reason)
    must not fan out the fact's order lines, so gross_revenue for the matched orders must be
    identical whether computed directly on fct_sales (ground truth, no bridge join, so fan-out is
    structurally impossible) or via the bridge join. Returns a row (fails) if the bridge join
    inflates (or deflates) gross_revenue for any matched order, or if the filter matches zero
    orders (a vacuous pass — e.g. a literal that no longer matches dim_sales_reason).
-#}
with promotion_orders as (
    select distinct bridge.sales_order_number
    from {{ ref('bridge_order_sales_reason') }} as bridge
    inner join {{ ref('dim_sales_reason') }} as reason
        on bridge.sales_reason_key = reason.sales_reason_key
    where reason.sales_reason_name = 'On Promotion'
),

matched_orders_count as (
    select count(*) as n from promotion_orders
),

direct_gross as (
    select round(sum(fact.gross_revenue), 2) as gross_direct
    from {{ ref('fct_sales') }} as fact
    inner join promotion_orders on fact.sales_order_number = promotion_orders.sales_order_number
),

bridge_joined_gross as (
    select round(sum(fact.gross_revenue), 2) as gross_via_bridge
    from {{ ref('fct_sales') }} as fact
    inner join {{ ref('bridge_order_sales_reason') }} as bridge
        on fact.sales_order_number = bridge.sales_order_number
    inner join {{ ref('dim_sales_reason') }} as reason
        on bridge.sales_reason_key = reason.sales_reason_key
    where reason.sales_reason_name = 'On Promotion'
)

select
    direct_gross.gross_direct,
    bridge_joined_gross.gross_via_bridge,
    matched_orders_count.n as matched_orders
from direct_gross
cross join bridge_joined_gross
cross join matched_orders_count
where
    direct_gross.gross_direct != bridge_joined_gross.gross_via_bridge
    or matched_orders_count.n = 0
