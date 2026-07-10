with credit_card as (
    select * from {{ ref('stg_adventure_works__creditcard') }}
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['credit_card_id']) }} as credit_card_key,
        credit_card_id,
        card_type
    from credit_card
)

select * from surrogate_keyed
