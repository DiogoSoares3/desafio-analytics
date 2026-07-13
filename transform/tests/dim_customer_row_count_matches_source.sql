-- P3-05 (ADR-0010): dim_customer must cover ALL sales channels, i.e. one row per source
-- customer (individual + store), not just online/individual customers. Fails while
-- dim_customer still filters to store_id is null.
with source_count as (
    select count(*) as n from {{ source('adventure_works', 'customer') }}
),

dim_count as (
    select count(*) as n from {{ ref('dim_customer') }}
)

select
    source_count.n as source_customer_count,
    dim_count.n as dim_customer_count
from source_count
cross join dim_count
where source_count.n != dim_count.n
