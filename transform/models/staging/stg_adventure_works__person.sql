with source as (
    select * from {{ source('adventure_works', 'person') }}
),

renamed as (
    select
        businessentityid as person_id,
        firstname as first_name,
        lastname as last_name,
        persontype as person_type
    from source
)

select * from renamed
