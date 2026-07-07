{% snapshot snap_customers %}

{{
    config(
        target_schema='warehouse',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='updated_at'
    )
}}

select
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    country,
    created_at,
    updated_at
from {{ ref('stg_customers') }}

{% endsnapshot %}