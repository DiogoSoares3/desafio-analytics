with source as (
    select * from {{ source('adventure_works', 'store') }}
),

renamed as (
    select
        businessentityid as store_id,
        name as store_name
    from source
)

select * from renamed
