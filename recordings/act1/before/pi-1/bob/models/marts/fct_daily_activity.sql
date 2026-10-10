-- grain: one row per calendar day (UTC)

with events as (

    select *
    from {{ ref('stg_events') }}

),

deduped as (

    -- stg_events is not deduplicated: mobile replays share event_id.
    -- keep the earliest ingested_at per event_id.
    select
        *,
        row_number() over (
            partition by event_id
            order by ingested_at asc
        ) as rn
    from events

),

events_deduped as (

    select
        event_id,
        user_id,
        event_type,
        platform,
        event_ts
    from deduped
    where rn = 1

),

daily as (

    select
        date_trunc('day', event_ts) as activity_date,
        count(*) as event_count,
        count(distinct user_id) as active_users
    from events_deduped
    group by 1

),

final as (

    select
        activity_date,
        active_users,
        event_count
    from daily

)

select * from final
order by activity_date
