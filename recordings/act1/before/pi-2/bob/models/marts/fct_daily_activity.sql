-- grain: one row per calendar day (UTC)
with events as (

    select *
    from {{ ref('stg_events') }}

),

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
        count(event_id) as event_count
    from daily
    group by activity_date
)

select *
from final
