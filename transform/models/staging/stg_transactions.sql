select
    cast(transaction_id as bigint)           as transaction_id,
    cast(account_id as integer)              as account_id,
    cast(transaction_ts as timestamp)        as transaction_ts,
    cast(transaction_ts as date)             as transaction_date,
    {{ cents_to_dollars('amount_cents') }}   as amount,
    lower(trim(category))                    as category,
    lower(trim(channel))                     as channel,
    lower(trim(status))                      as status,
    cast(_loaded_at as timestamp)            as loaded_at
from {{ source('raw', 'transactions') }}
