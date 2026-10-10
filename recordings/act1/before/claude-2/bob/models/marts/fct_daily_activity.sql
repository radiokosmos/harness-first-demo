-- grain: one row per UTC calendar day with at least one event
-- source grain: stg_events is one row per ingested event, with duplicates on event_id (mobile replays)

with events as (

    select * from {{ ref('stg_events') }}

),

deduped as (

    select
        event_id,
        user_id,
        event_ts,
        row_number() over (
            partition by event_id
            order by ingested_at asc
        ) as row_num
    from events

),

daily as (

    select
        cast(event_ts at time zone 'UTC' as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from deduped
    where row_num = 1
    group by 1

)

select
    activity_date,
    active_users,
    event_count
from daily
