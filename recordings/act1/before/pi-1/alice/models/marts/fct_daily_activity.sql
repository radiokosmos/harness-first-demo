-- grain: one row per calendar day (activity_date)

with events as (

    select *
    from {{ ref('stg_events') }}

),

deduped as (

    -- stg_events has duplicates from mobile replays; keep the earliest ingested_at per event_id
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

daily as (

    select
        date_trunc('day', event_ts) as activity_date,
        user_id,
        event_id
    from deduped
    where rn = 1

),

final as (

    select
        activity_date,
        count(distinct user_id) as active_users,
        count(event_id) as event_count
    from daily
    group by activity_date

)

select *
from final
order by activity_date
