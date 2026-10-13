-- grain: one row per day

with events as (

    select
        event_id,
        user_id,
        event_ts,
        ingested_at
    from {{ ref('stg_events') }}

),

deduped as (

    -- mobile replays share event_id; keep the earliest ingested_at
    select *
    from events
    qualify row_number() over (partition by event_id order by ingested_at) = 1

),

daily as (

    select
        -- not cast(event_ts as date): the session is America/Los_Angeles
        cast(timezone('UTC', event_ts) as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from deduped
    group by 1

)

select
    activity_date,
    active_users,
    event_count
from daily
