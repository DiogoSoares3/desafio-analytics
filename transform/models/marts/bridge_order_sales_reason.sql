with order_sales_reason as (
    select * from {{ ref('stg_adventure_works__salesorderheadersalesreason') }}
),

sales_order_header as (
    select * from {{ ref('stg_adventure_works__salesorderheader') }}
),

sales_reason as (
    select * from {{ ref('dim_sales_reason') }}
),

bridged as (
    select
        sales_order_header.sales_order_number,
        sales_reason.sales_reason_key
    from order_sales_reason
    inner join sales_order_header
        on order_sales_reason.sales_order_id = sales_order_header.sales_order_id
    inner join sales_reason
        on order_sales_reason.sales_reason_id = sales_reason.sales_reason_id
)

select * from bridged
