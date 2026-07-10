with address as (
    select * from {{ ref('stg_adventure_works__address') }}
),

state_province as (
    select * from {{ ref('stg_adventure_works__stateprovince') }}
),

country_region as (
    select * from {{ ref('stg_adventure_works__countryregion') }}
),

joined as (
    select distinct
        address.city,
        state_province.state_province_name as state_province,
        country_region.country_name as country
    from address
    inner join state_province
        on address.state_province_id = state_province.state_province_id
    inner join country_region
        on state_province.country_region_code = country_region.country_region_code
),

surrogate_keyed as (
    select
        {{
            dbt_utils.generate_surrogate_key(['city', 'state_province', 'country'])
        }} as geography_key,
        city,
        state_province,
        country
    from joined
)

select * from surrogate_keyed
