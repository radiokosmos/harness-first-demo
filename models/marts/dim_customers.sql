-- grain: one row per customer who has contacted support

with tickets as (

    select
        customer_id,
        created_at,
        channel
    from {{ source('raw', 'support_tickets') }}

)

select
    customer_id,
    min(created_at) as first_contact_at,
    count(*) as tickets,
    count(distinct channel) as channels
from tickets
group by 1
