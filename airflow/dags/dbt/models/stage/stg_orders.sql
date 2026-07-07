{{ config(
    materialized='view'
) }}

with ranked_orders as (
select
    order_id,
    customer_id,
    product_id,
    cast(order_date as date) as order_date,
    quantity,
    unit_price,
    coalesce(discount, 0)   as discount,
    total_amount,
    coalesce(trim(lower(order_status)), 'unknown')     as order_status,
    coalesce(trim(lower(payment_method)), 'unknown')   as payment_method,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at,
    row_number() over (
            partition by order_id
            order by updated_at desc
        ) as rn
from {{ source('raw', 'orders') }}

)

select
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    discount,
    total_amount,
    order_status,
    payment_method,
    created_at,
    updated_at
    
from ranked_orders
where rn = 1