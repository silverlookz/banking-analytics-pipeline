with accounts as (
    select
        customer_id,
        count(*)                                  as accounts_total,
        count(*) filter (where is_active)         as accounts_active,
        count(distinct product_type)              as products_held,
        sum(credit_limit)                         as total_credit_limit
    from {{ ref('stg_accounts') }}
    group by 1
),

activity as (
    select
        customer_id,
        count(*)                                  as lifetime_transactions,
        sum(inflow)                               as lifetime_inflow,
        sum(outflow)                              as lifetime_outflow,
        max(transaction_date)                     as last_transaction_date,
        avg(case when is_digital then 1 else 0 end) as digital_share
    from {{ ref('fct_transactions') }}
    group by 1
)

select
    c.customer_id,
    c.first_name || ' ' || c.last_name            as customer_name,
    c.email is not null                           as has_email,
    c.segment,
    c.home_branch_code,
    c.customer_since,
    date_diff('year', c.customer_since, date '2025-12-31') as tenure_years,
    case
        when c.birth_year is null then 'unknown'
        when 2025 - c.birth_year < 35 then '18-34'
        when 2025 - c.birth_year < 55 then '35-54'
        else '55+'
    end                                           as age_band,
    coalesce(a.accounts_total, 0)                 as accounts_total,
    coalesce(a.accounts_active, 0)                as accounts_active,
    coalesce(a.products_held, 0)                  as products_held,
    coalesce(a.total_credit_limit, 0)             as total_credit_limit,
    coalesce(t.lifetime_transactions, 0)          as lifetime_transactions,
    round(coalesce(t.lifetime_inflow, 0), 2)      as lifetime_inflow,
    round(coalesce(t.lifetime_outflow, 0), 2)     as lifetime_outflow,
    t.last_transaction_date,
    round(coalesce(t.digital_share, 0), 3)        as digital_share,
    coalesce(t.last_transaction_date < date '2025-10-01', true) as is_dormant
from {{ ref('stg_customers') }} c
left join accounts a using (customer_id)
left join activity t using (customer_id)
