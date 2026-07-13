with customer as (
    select * from {{ ref('stg_adventure_works__customer') }}
),

person as (
    select * from {{ ref('stg_adventure_works__person') }}
),

store as (
    select * from {{ ref('stg_adventure_works__store') }}
),

individual_customers as (
    select
        customer.customer_id,
        'individual' as customer_type,
        person.first_name || ' ' || person.last_name as full_name
    from customer
    inner join person
        on customer.person_id = person.person_id
    where customer.store_id is null
),

store_customers as (
    select
        customer.customer_id,
        'store' as customer_type,
        store.store_name as full_name
    from customer
    inner join store
        on customer.store_id = store.store_id
    where customer.store_id is not null
),

all_customers as (
    select * from individual_customers
    union all
    select * from store_customers
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }} as customer_key,
        customer_id,
        customer_type,
        full_name
    from all_customers
)

select * from surrogate_keyed
