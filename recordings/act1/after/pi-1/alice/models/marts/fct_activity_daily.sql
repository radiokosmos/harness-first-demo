-- grain: one row per day

with events as (

    select
        event_id,
        user_id,
        event_ts
    from {{ ref('stg_events') }}

),

daily as (

    select
        cast(event_ts as date) as activity_date,
        user_id,
        event_id
    from events

),

aggregated as (

    select
        activity_date,
        count(distinct user_id) as active_users,
        count(event_id) as event_count
    from daily
    group by activity_date

)

select
    activity_date,
    active_users,
    event_count
from aggregated
order by activity_date
