{{ config(
    materialized='incremental',
    unique_key='customer_id',
    incremental_strategy='merge'
) }}



    select
        customer_id,
        trim(first_name) as first_name,
        trim(last_name) as last_name,
        lower(email) as email,
        phone,
        address,
        city,
        state,
        country,
        coalesce(acquisition_channel,'unknown') as acquisition_channel,
        signup_date,
        created_at,
        updated_at
    from {{ source('raw', 'customers') }}

    {% if is_incremental() %}
    where updated_at > (select coalesce(max(updated_at), '1900-01-01') from {{ this }})
    or customer_id not in (select customer_id from {{ this }})
    {% endif %}