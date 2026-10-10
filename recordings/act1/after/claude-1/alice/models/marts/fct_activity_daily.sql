-- Grain: one row per UTC day with at least one event.
-- Source stg_events: one row per ingested event, mobile replays duplicate event_id, so dedup first.

with events as (

    select
        event_id,
        user_id,
        event_ts,
    from {{ ref('stg_events') }}

),

deduped as (

    select
        event_id,
        user_id,
        event_ts,
    from events
    qualify row_number() over (partition by event_id order by event_ts) = 1

),

final as (

    select
        cast(timezone('UTC', event_ts) as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as event_count,
    from deduped
    group by 1

)

select
    activity_date,
    active_users,
    event_count,
from final
