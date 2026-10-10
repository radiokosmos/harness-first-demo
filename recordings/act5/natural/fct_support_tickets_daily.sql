-- grain: one row per day and channel

with tickets as (

    select
        channel,
        created_at
    from {{ source('raw', 'support_tickets') }}

),

daily as (

    select
        cast(timezone('UTC', created_at) as date) as ticket_date,
        channel,
        count(*) as ticket_count
    from tickets
    group by 1, 2

)

select
    ticket_date || '_' || channel as ticket_date_channel_id,
    ticket_date,
    channel,
    ticket_count
from daily
