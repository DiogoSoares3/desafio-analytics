-- P3-05 (ADR-0010): dim_credit_card must carry an explicit "N/A" member so reseller order
-- lines (no CreditCardID) resolve a not_null credit_card_key on fct_sales. Fails (returns 0
-- rows treated as failure via having count = 0) while no such row exists.
with na_member as (
    select * from {{ ref('dim_credit_card') }}
    where card_type = 'N/A'
)

select 1 as missing_na_member
where (select count(*) from na_member) = 0
