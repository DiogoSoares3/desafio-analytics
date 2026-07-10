with source as (
    select * from {{ source('adventure_works', 'salesorderheader') }}
),

renamed as (
    select
        salesorderid as sales_order_id,
        salesordernumber as sales_order_number,
        cast(orderdate as date) as order_date,
        status as status_code,
        onlineorderflag as online_order_flag,
        customerid as customer_id,
        creditcardid as credit_card_id,
        shiptoaddressid as ship_to_address_id,
        billtoaddressid as bill_to_address_id,
        subtotal,
        taxamt as tax_amount,
        freight
    from source
),

online_only as (
    select * from renamed
    where online_order_flag
)

select * from online_only
