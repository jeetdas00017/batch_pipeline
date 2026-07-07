-- ---------------------------------------------------------------------
-- dim_customers
-- Reads the SCD2 snapshot (full history) and exposes a clean dimension
-- with a surrogate key, validity window, and an `is_current` flag.
-- ---------------------------------------------------------------------
{{ config(
    materialized='incremental',
    unique_key='customer_sk',
    incremental_strategy='merge'
) }}

select
    warehouse.customer_sk.nextval as customer_sk, 
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    country,
    DBT_SCD_ID,
    dbt_updated_at,
    dbt_valid_from as effective_from,
    dbt_valid_to as effective_to,
    case when dbt_valid_to is null then true else false end as is_current

from {{ ref('snap_customers') }}
