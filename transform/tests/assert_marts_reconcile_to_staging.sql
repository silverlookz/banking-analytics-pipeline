-- Reconciliation: posted transaction count in the fact must match staging.
with staged as (select count(*) as n from {{ ref('stg_transactions') }} where status = 'posted'),
     fact   as (select count(*) as n from {{ ref('fct_transactions') }})
select * from staged, fact where staged.n <> fact.n
