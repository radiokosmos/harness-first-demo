-- grain: one row per calendar day (UTC)
with events as (

    select * from {{ ref('stg_events') }}

),

-- stg_events is not deduplicated (mobile replays share event_id);
-- keep the earliest ingested_at per event_id
deduped as (

    select
        event_id,
        user_id,
        event_ts,
        row_number() over (
            partition by event_id
            order by ingested_at
        ) as rn
    from events

),

daily_events as (

    select
        cast(event_ts as date) as event_date,
        user_id,
        event_id
    from deduped
    where rn = 1

),

final as (

    select
        event_date,
        count(distinct user_id) as active_users,
        count(event_id) as event_count
    from daily_events
    group by event_date

)

select
    event_date,
    active_users,
    event_count
from final
order by event_date
