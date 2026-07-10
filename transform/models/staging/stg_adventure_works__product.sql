with source as (
    select * from {{ source('adventure_works', 'product') }}
),

renamed as (
    select
        productid as product_id,
        name as product_name,
        productnumber as product_number,
        productsubcategoryid as product_subcategory_id
    from source
)

select * from renamed
