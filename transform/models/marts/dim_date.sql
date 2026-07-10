{%- set start_date_expr -%}
    (select cast(min(order_date) as date) from {{ ref('stg_adventure_works__salesorderheader') }})
{%- endset -%}

{%- set end_date_expr -%}
    (select cast(max(order_date) as date) + interval 1 day from {{ ref('stg_adventure_works__salesorderheader') }})
{%- endset -%}

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date=start_date_expr,
        end_date=end_date_expr
    ) }}
),

calendar as (
    select
        cast(date_day as date) as date_day,
        extract(year from date_day) as year,
        extract(month from date_day) as month_number,
        strftime(date_day, '%B') as month_name,
        strftime(date_day, '%Y-%m') as year_month,
        strftime(date_day, '%A') as day_of_week,
        extract(dow from date_day) in (0, 6) as is_weekend
    from date_spine
),

surrogate_keyed as (
    select
        {{ dbt_utils.generate_surrogate_key(['date_day']) }} as date_key,
        date_day,
        year,
        month_number,
        month_name,
        year_month,
        day_of_week,
        is_weekend
    from calendar
)

select * from surrogate_keyed
