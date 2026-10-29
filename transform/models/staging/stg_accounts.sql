select
    cast(account_id as integer)                  as account_id,
    cast(customer_id as integer)                 as customer_id,
    lower(trim(product_type))                    as product_type,
    cast(opened_on as date)                      as opened_on,
    try_cast(nullif(closed_on, '') as date)      as closed_on,
    nullif(closed_on, '') is null                as is_active,
    {{ cents_to_dollars('credit_limit_cents') }} as credit_limit,
    product_type in ('credit_card', 'line_of_credit') as is_credit_product
from {{ source('raw', 'accounts') }}
