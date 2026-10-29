{#- Use the folder schema name directly (staging / intermediate / marts) instead of target_schema prefix. -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
