{% snapshot snap_products %}

{{
    config(
      target_schema='snapshots',
      unique_key='product_id',
      strategy='timestamp',
      updated_at='updated_at',
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
    updated_at
from {{ ref('stg_products') }}

{% endsnapshot %}
