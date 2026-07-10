with product as (
    select * from {{ ref('stg_adventure_works__product') }}
),

product_subcategory as (
    select * from {{ ref('stg_adventure_works__productsubcategory') }}
),

product_category as (
    select * from {{ ref('stg_adventure_works__productcategory') }}
),

joined as (
    select
        product.product_id,
        product.product_name,
        product.product_number,
        product_subcategory.subcategory_name,
        product_category.category_name
    from product
    left join product_subcategory
        on product.product_subcategory_id = product_subcategory.product_subcategory_id
    left join product_category
        on product_subcategory.product_category_id = product_category.product_category_id
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['product_id']) }} as product_key,
        product_id,
        product_name,
        product_number,
        subcategory_name,
        category_name
    from joined
)

select * from surrogate_keyed
