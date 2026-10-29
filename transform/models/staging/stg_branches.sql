select
    upper(trim(branch_code))  as branch_code,
    trim(branch_name)         as branch_name,
    upper(trim(province))     as province
from {{ source('raw', 'branches') }}
