-- grain: one row per UTC calendar day
with events as (

    select
        event_id,
        user_id,
        event_ts,
        ingested_at
    from {{ ref('stg_events') }}

),

deduped as (

    select
        event_id,
        user_id,
        event_ts
    from events
    qualify row_number() over (partition by event_id order by ingested_at) = 1

),

events_by_day as (

    select
        cast(event_ts at time zone 'UTC' as date) as activity_date,
        event_id,
        user_id
    from deduped

),

final as (

    select
        activity_date,
        count(distinct user_id) as active_users,
        count(*) as events
    from events_by_day
    group by activity_date

)

select
    activity_date,
    active_users,
    events
from final
