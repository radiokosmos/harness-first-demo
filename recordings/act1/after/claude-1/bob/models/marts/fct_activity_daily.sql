-- Grain: one row per UTC calendar day.
-- Source stg_events has mobile-replay duplicates: one row per event_id after dedup (earliest ingested_at kept).

with events as (

    select
        event_id,
        user_id,
        event_ts,
        ingested_at,
    from {{ ref('stg_events') }}

),

deduped_events as (

    select
        event_id,
        user_id,
        event_ts,
    from events
    qualify row_number() over (partition by event_id order by ingested_at asc) = 1

),

daily as (

    select
        cast(event_ts at time zone 'UTC' as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as events,
    from deduped_events
    group by 1

),

final as (

    select
        activity_date,
        active_users,
        events,
    from daily

)

select
    activity_date,
    active_users,
    events,
from final
