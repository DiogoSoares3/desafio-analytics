{{ config(severity='error') }}

{#-
    P3-04 / ADR-0003: fct_sales carries no reason FK; reason-filtered analysis joins through
    bridge_order_sales_reason (grain: order x reason). A single-reason filter (e.g.
    "Promotion") must not fan out the fact's order lines, so gross_revenue for the matched
    orders must be identical whether computed directly on fct_sales (ground truth, no bridge
    join, so fan-out is structurally impossible) or via the bridge join. Returns a row (fails)
    if the bridge join inflates (or deflates) gross_revenue for any matched order.
-#}
with promotion_orders as (
    select distinct bridge.sales_order_number
    from {{ ref('bridge_order_sales_reason') }} as bridge
    inner join {{ ref('dim_sales_reason') }} as reason
        on bridge.sales_reason_key = reason.sales_reason_key
    where reason.sales_reason_name = 'Promotion'
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
    where reason.sales_reason_name = 'Promotion'
)

select
    direct_gross.gross_direct,
    bridge_joined_gross.gross_via_bridge
from direct_gross
cross join bridge_joined_gross
where direct_gross.gross_direct != bridge_joined_gross.gross_via_bridge
