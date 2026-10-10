-- grain: one row per day

with events as (
    select *
    from {{ ref('stg_events') }}
),

-- stg_events is not deduplicated (mobile replays repeat an event_id);
-- keep the earliest ingested_at per event_id, per models/staging/AGENTS.md
deduped as (
    select
        event_id,
        user_id,
        event_ts,
        row_number() over (
            partition by event_id
            order by ingested_at asc
        ) as rn
    from events
),

daily as (
    select
        cast(event_ts as date) as activity_date,
        user_id,
        event_id
    from deduped
    where rn = 1
),

final as (
    select
        activity_date,
        count(distinct user_id) as active_users,
        count(distinct event_id) as event_count
    from daily
    group by activity_date
)

select
    activity_date,
    active_users,
    event_count
from final
order by activity_date
