-- grain: one row per calendar day (UTC)

with events as (

    select
        event_id,
        user_id,
        event_ts,
        ingested_at
    from {{ ref('stg_events') }}

),

deduped as (

    -- stg_events is not deduplicated; mobile replays share event_id.
    -- keep the earliest ingested_at per event_id.
    select
        event_id,
        user_id,
        event_ts,
        ingested_at,
        row_number() over (
            partition by event_id
            order by ingested_at asc
        ) as rn
    from events

),

final as (

    select
        -- event_ts is UTC; anchor the day boundary to UTC regardless of session timezone
        cast(event_ts at time zone 'UTC' as date) as activity_date,
        count(*) as event_count,
        count(distinct user_id) as active_users
    from deduped
    where rn = 1
    group by 1

)

select
    activity_date,
    active_users,
    event_count
from final
