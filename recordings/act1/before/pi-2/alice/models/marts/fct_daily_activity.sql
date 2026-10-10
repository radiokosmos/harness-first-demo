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

    -- stg_events has duplicates from mobile replays; keep the earliest
    -- ingested_at row per event_id
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
        -- event_ts is stored in UTC, but the session timezone is not;
        -- force UTC before truncating to a date
        cast(timezone('UTC', event_ts) as date) as activity_date,
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
    group by 1

)

select * from final
