select
    order_id,
    customer_id,
    product_id,
    order_date,
    quantity,
    unit_price,
    coalesce(discount, 0)   as discount,
    total_amount,
    lower(order_status)     as order_status,
    lower(payment_method)   as payment_method,
    created_at,
    updated_at
from {{ source('raw', 'orders') }}
where order_id is not null
    and quantity >= 0
    and total_amount >= 0

