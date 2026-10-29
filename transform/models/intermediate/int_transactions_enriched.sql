-- Posted transactions joined to account, customer and branch context.
select
    t.transaction_id,
    t.transaction_ts,
    t.transaction_date,
    date_trunc('month', t.transaction_date)        as transaction_month,
    t.amount,
    case when t.amount >= 0 then t.amount else 0 end  as inflow,
    case when t.amount < 0 then t.amount else 0 end   as outflow,
    t.category,
    t.channel,
    t.channel in ('mobile', 'online')              as is_digital,
    t.loaded_at,
    a.account_id,
    a.product_type,
    c.customer_id,
    c.segment,
    b.branch_code,
    b.branch_name,
    b.province
from {{ ref('stg_transactions') }} t
join {{ ref('stg_accounts') }}  a on a.account_id = t.account_id
join {{ ref('stg_customers') }} c on c.customer_id = a.customer_id
join {{ ref('stg_branches') }}  b on b.branch_code = c.home_branch_code
where t.status = 'posted'
