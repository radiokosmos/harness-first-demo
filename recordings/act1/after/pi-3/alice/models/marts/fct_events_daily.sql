-- grain: one row per day

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
    qualify row_number() over (
        partition by event_id
        order by ingested_at asc
    ) = 1
),

daily as (
    select
        cast(event_ts as date) as event_date,
        user_id
    from deduped
),

final as (
    select
        event_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from daily
    group by event_date
)

select
    event_date,
    active_users,
    event_count
from final
order by event_date
