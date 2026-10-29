-- Net flow must always equal inflow + outflow for every branch-month.
select *
from {{ ref('mart_branch_monthly_kpis') }}
where abs(net_flow - (inflow + outflow)) > 0.05
