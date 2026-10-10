-- Grain: one row per UTC calendar day (event_date).
-- stg_events is not deduplicated, so keep the earliest ingested_at per event_id first.

with events as (

    select * from {{ ref('stg_events') }}

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
        count(*) as event_count,
    from deduped
    group by 1

)

select
    event_date,
    active_users,
    event_count,
from daily
