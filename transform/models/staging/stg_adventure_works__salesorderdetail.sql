with source as (
    select * from {{ source('adventure_works', 'salesorderdetail') }}
),

renamed as (
    select
        salesorderdetailid as sales_order_detail_id,
        salesorderid as sales_order_id,
        productid as product_id,
        orderqty as order_qty,
        unitprice as unit_price,
        unitpricediscount as unit_price_discount,
        linetotal as line_total,
        specialofferid as special_offer_id
    from source
)

select * from renamed
