{{ config(severity='error') }}

{#-
    Asserts dim_date is a gap-free daily calendar: every date has a predecessor
    exactly one day earlier (except the first date in the spine). Returns
    offending rows; zero rows = pass (P2-04 acceptance scenario).
-#}
with ordered_dates as (
    select
        date_day,
        lag(date_day) over (order by date_day) as previous_date_day
    from {{ ref('dim_date') }}
),

gaps as (
    select
        date_day,
        previous_date_day,
        date_day - previous_date_day as day_gap
    from ordered_dates
    where
        previous_date_day is not null
        and date_day - previous_date_day <> 1
)

select * from gaps
