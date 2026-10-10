-- Grain: one row per UTC day with at least one event.
-- Source grain: stg_events has one row per ingested event, with duplicates from mobile replays.

with events as (

    select * from {{ ref('stg_events') }}

),

deduped as (

    select
        event_id,
        user_id,
        event_ts
    from events
    qualify row_number() over (partition by event_id order by ingested_at asc) = 1

),

daily as (

    select
        cast(timezone('UTC', event_ts) as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as events
    from deduped
    group by 1

)

select
    activity_date,
    active_users,
    events
from daily
