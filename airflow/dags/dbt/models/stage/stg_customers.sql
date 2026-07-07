{{ config(
    materialized='view'
) }}

with ranked_customers as (

    select
        customer_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(email) as email,
        phone,
        city,
        country,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at,

        row_number() over (
            partition by customer_id
            order by updated_at desc
        ) as rn

    from {{ source('raw', 'customers') }}

)

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

from ranked_customers

where rn = 1