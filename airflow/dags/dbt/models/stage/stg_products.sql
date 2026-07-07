{{ config(
    materialized='view'
) }}
with ranked_products as (
    select
        product_id,
        product_name,
        category,
        sub_category,
        brand,
        price,
        cost,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at,
    
        row_number() over (
            partition by product_id
            order by updated_at desc
        ) as rn

    from {{ source('raw', 'products') }}

)
select
    product_id,
    product_name,
    category,
    sub_category,
    brand,
    price,
    cost,
    created_at,
    updated_at
    
from ranked_products
where rn = 1