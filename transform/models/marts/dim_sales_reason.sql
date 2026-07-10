with sales_reason as (
    select * from {{ ref('stg_adventure_works__salesreason') }}
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['sales_reason_id']) }} as sales_reason_key,
        sales_reason_id,
        sales_reason_name,
        sales_reason_type
    from sales_reason
)

select * from surrogate_keyed
