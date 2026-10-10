-- grain: one row per calendar day (UTC)
with

events as (

    select
        event_id,
        user_id,
        event_ts,
        ingested_at
    from {{ ref('stg_events') }}

),

-- stg_events is not deduplicated: mobile replays share event_id.
-- keep the earliest ingested_at per event_id.
deduped as (

    select
        *,
        row_number() over (
            partition by event_id
            order by ingested_at asc
        ) as rn
    from events

),

daily as (

    select
        cast(event_ts as date) as activity_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from deduped
    where rn = 1
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
