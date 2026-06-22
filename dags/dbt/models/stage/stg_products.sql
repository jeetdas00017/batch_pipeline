{{
    config(
        materialized='incremental',
        unique_key='product_id',
        incremental_strategy='merge'
    )
}}

select
    product_id,
    product_name,
    category,
    sub_category,
    brand,
    price,
    cost,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at
from {{ source('raw', 'products') }}

{% if is_incremental() %}
where cast(updated_at as timestamp) > (select coalesce(max(cast(updated_at as timestamp)), '1900-01-01') from {{ this }})
   or product_id not in (select product_id from {{ this }})
{% endif %}