-- One row per customer: CRM re-syncs create duplicates, keep the latest version.
with ranked as (
    select
        *,
        row_number() over (
            partition by customer_id order by cast(_updated_at as timestamp) desc
        ) as _rn
    from {{ source('raw', 'customers') }}
)

select
    cast(customer_id as integer)            as customer_id,
    trim(first_name)                        as first_name,
    trim(last_name)                         as last_name,
    nullif(lower(trim(email)), '')          as email,
    try_cast(nullif(birth_year, '') as integer) as birth_year,
    lower(trim(segment))                    as segment,
    upper(trim(home_branch))                as home_branch_code,
    cast(opened_on as date)                 as customer_since,
    cast(_updated_at as timestamp)          as updated_at
from ranked
where _rn = 1
