with customer as (
    select * from {{ ref('stg_adventure_works__customer') }}
),

person as (
    select * from {{ ref('stg_adventure_works__person') }}
),

online_customers as (
    select * from customer
    where store_id is null
),

joined as (
    select
        online_customers.customer_id,
        person.first_name || ' ' || person.last_name as full_name
    from online_customers
    inner join person
        on online_customers.person_id = person.person_id
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
        customer_id,
        full_name
    from joined
)

select * from surrogate_keyed
