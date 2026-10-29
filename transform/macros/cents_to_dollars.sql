{% macro cents_to_dollars(column, precision=2) -%}
    round(cast({{ column }} as double) / 100, {{ precision }})
{%- endmacro %}
