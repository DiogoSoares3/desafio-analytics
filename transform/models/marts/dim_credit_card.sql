with credit_card as (
    select * from {{ ref('stg_adventure_works__creditcard') }}
),

-- ADR-0010: card-less reseller order lines need a real row to resolve a not_null
-- credit_card_key FK on fct_sales; credit_card_id null distinguishes it as synthetic.
na_member as (
    select
        cast(null as integer) as credit_card_id,
        'N/A' as card_type
),

all_credit_cards as (
    select
        credit_card_id,
        card_type
    from credit_card
    union all
    select
        credit_card_id,
        card_type
    from na_member
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['credit_card_id']) }} as credit_card_key,
        credit_card_id,
        card_type
    from all_credit_cards
)

select * from surrogate_keyed
