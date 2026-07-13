with order_lines as (
    select * from {{ ref('int_sales__order_lines') }}
)

select
    sales_fact_key,
    product_key,
    customer_key,
    date_key,
    geography_key,
    credit_card_key,
    order_status_key,
    sales_order_number,
    sales_order_line_number,
    is_online,
    order_qty,
    gross_revenue,
    discount_amount,
    net_revenue
from order_lines
