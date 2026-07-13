{{ config(severity='error') }}

{#-
    P3-04 / ADR-0001: net_revenue (gross_revenue - discount_amount) must reconcile to source
    salesorderdetail.LineTotal exactly (zero tolerance), across all channels and all order
    dates. Returns a row (fails) unless the two sums match to the cent.
-#}
with fact_net as (
    select round(sum(net_revenue), 2) as total_net_revenue
    from {{ ref('fct_sales') }}
),

source_line_total as (
    select round(sum(line_total), 2) as total_line_total
    from {{ ref('stg_adventure_works__salesorderdetail') }}
)

select
    fact_net.total_net_revenue,
    source_line_total.total_line_total
from fact_net
cross join source_line_total
where fact_net.total_net_revenue != source_line_total.total_line_total
