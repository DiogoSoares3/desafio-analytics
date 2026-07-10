with order_status as (
    select * from {{ ref('order_status') }}
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['status_code']) }} as order_status_key,
        status_code,
        status_label
    from order_status
)

select * from surrogate_keyed
