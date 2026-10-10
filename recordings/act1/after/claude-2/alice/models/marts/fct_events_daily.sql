-- Grain: one row per UTC day (event_date), built from deduplicated stg_events (one row per event_id).
with events as (

    select
        event_id,
        user_id,
        event_ts,
        ingested_at,
    from {{ ref('stg_events') }}

),

deduped as (

    select
        event_id,
        user_id,
        event_ts,
    from events
    qualify row_number() over (partition by event_id order by ingested_at asc) = 1

),

daily as (

    select
        cast(event_ts at time zone 'UTC' as date) as event_date,
        count(distinct user_id) as active_users,
        count(*) as events,
    from deduped
    group by 1

)

select
    event_date,
    active_users,
    events,
from daily
