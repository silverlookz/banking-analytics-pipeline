select
    transaction_month,
    branch_code,
    any_value(branch_name)                       as branch_name,
    any_value(province)                          as province,
    count(distinct customer_id)                  as active_customers,
    count(*)                                     as transactions,
    round(sum(inflow), 2)                        as inflow,
    round(sum(outflow), 2)                       as outflow,
    round(sum(amount), 2)                        as net_flow,
    round(avg(case when is_digital then 1.0 else 0 end), 3) as digital_share
from {{ ref('fct_transactions') }}
group by 1, 2
