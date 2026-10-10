-- grain: one row per utc calendar day

with events as (

    select *
    from {{ ref('stg_events') }}

),

deduped as (

    -- mobile replays share event_id; keep the earliest ingested_at
    select *
    from events
    qualify row_number() over (
        partition by event_id
        order by ingested_at asc
    ) = 1

),

daily as (

    select
        cast(timezone('UTC', event_ts) as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from deduped
    group by 1

)

select
    activity_date,
    active_users,
    event_count
from daily
order by activity_date
