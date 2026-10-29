select
    transaction_month,
    segment,
    category,
    count(*)                         as transactions,
    round(-sum(outflow), 2)          as spend,
    round(-avg(outflow), 2)          as avg_ticket
from {{ ref('fct_transactions') }}
where amount < 0
group by 1, 2, 3
