{{ config(severity='error') }}

{#-
    P3-04 / ADR-0001: the régua headline. 2011 gross sales (all channels, pre-discount,
    pre-tax, pre-freight line revenue = UnitPrice * OrderQty) must reconcile to the audited
    figure exactly (zero tolerance). Returns a row (fails) unless the 2011 gross_revenue sum
    equals 12646112.16 to the cent.
-#}
with fact as (
    select * from {{ ref('fct_sales') }}
),

date_dim as (
    select * from {{ ref('dim_date') }}
),

gross_2011 as (
    select round(sum(fact.gross_revenue), 2) as total_gross_2011
    from fact
    inner join date_dim on fact.date_key = date_dim.date_key
    where date_dim.year = 2011
)

select *
from gross_2011
where total_gross_2011 != 12646112.16
