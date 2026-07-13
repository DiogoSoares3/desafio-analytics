with detail as (
    select * from {{ ref('stg_adventure_works__salesorderdetail') }}
),

header as (
    select * from {{ ref('stg_adventure_works__salesorderheader') }}
),

address as (
    select * from {{ ref('stg_adventure_works__address') }}
),

state_province as (
    select * from {{ ref('stg_adventure_works__stateprovince') }}
),

country_region as (
    select * from {{ ref('stg_adventure_works__countryregion') }}
),

-- All channels (ADR-0010) — no online_order_flag filter here; is_online is a fact attribute.
joined as (
    select
        detail.sales_order_detail_id,
        detail.product_id,
        detail.order_qty,
        detail.unit_price,
        detail.unit_price_discount,
        header.sales_order_id,
        header.sales_order_number,
        header.order_date,
        header.status_code,
        header.online_order_flag as is_online,
        header.customer_id,
        header.credit_card_id,
        address.city,
        state_province.state_province_name as state_province,
        country_region.country_name as country
    from detail
    inner join header
        on detail.sales_order_id = header.sales_order_id
    left join address
        on header.ship_to_address_id = address.address_id
    left join state_province
        on address.state_province_id = state_province.state_province_id
    left join country_region
        on state_province.country_region_code = country_region.country_region_code
),

keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['sales_order_detail_id']) }} as sales_fact_key,
        {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
        {{ dbt_utils.generate_surrogate_key(['order_date']) }} as date_key,
        {{
            dbt_utils.generate_surrogate_key(['city', 'state_province', 'country'])
        }} as geography_key,
        {{ dbt_utils.generate_surrogate_key(['credit_card_id']) }} as credit_card_key,
        {{ dbt_utils.generate_surrogate_key(['status_code']) }} as order_status_key,
        sales_order_number,
        row_number() over (
            partition by sales_order_id order by sales_order_detail_id
        ) as sales_order_line_number,
        is_online,
        order_qty,
        unit_price * order_qty as gross_revenue,
        unit_price_discount * unit_price * order_qty as discount_amount,
        (unit_price * order_qty) - (unit_price_discount * unit_price * order_qty) as net_revenue
    from joined
)

select * from keyed
