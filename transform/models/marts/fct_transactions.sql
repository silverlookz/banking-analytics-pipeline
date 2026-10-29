{{ config(materialized='incremental', unique_key='transaction_id', on_schema_change='append_new_columns') }}

select * from {{ ref('int_transactions_enriched') }}

{% if is_incremental() %}
  -- 3-day lookback catches late-arriving records
  where loaded_at > (select max(loaded_at) - interval 3 day from {{ this }})
{% endif %}
