{#- Lightweight stand-in for dbt_utils.unique_combination_of_columns, so the project has no package dependency. -#}
{% test dbt_utils_unique_combination(model, combination) %}
select {{ combination }} as combo, count(*) as n
from {{ model }}
group by 1
having count(*) > 1
{% endtest %}
