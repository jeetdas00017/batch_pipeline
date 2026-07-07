-- ---------------------------------------------------------------------
-- dim_products
-- Reads the SCD2 snapshot (full history) and exposes a clean dimension
-- with a surrogate key, validity window, and an `is_current` flag.
-- ---------------------------------------------------------------------
{{ config(
    materialized='incremental',
    unique_key='product_sk',
    incremental_strategy='merge'
) }}

select
    warehouse.product_sk.nextval as product_sk,
    product_id,
    product_name,
    category,
    sub_category,
    brand,
    price,
    cost,
    dbt_valid_from as effective_from,
    dbt_valid_to as effective_to,
    case when dbt_valid_to is null then true else false end as is_current

from {{ ref('snap_products') }}
