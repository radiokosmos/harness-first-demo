-- grain: one row per UTC day
-- source grain: stg_events is one row per ingested event; mobile replays repeat event_id

with events as (

    select * from {{ ref('stg_events') }}

),

deduped as (

    select
        event_id,
        user_id,
        event_ts,
        row_number() over (partition by event_id order by ingested_at asc) as rn
    from events

),

daily as (

    select
        cast(timezone('UTC', event_ts) as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from deduped
    where rn = 1
    group by 1

)

select
    activity_date,
    active_users,
    event_count
from daily
