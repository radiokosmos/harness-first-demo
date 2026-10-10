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

    -- stg_events has duplicates from mobile replays;
    -- keep the earliest ingested_at per event_id
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
        cast(event_ts as date) as activity_date,
        user_id,
        event_id
    from deduped

),

final as (

    select
        activity_date,
        count(distinct user_id) as active_users,
        count(distinct event_id) as event_count
    from daily
    group by activity_date

)

select * from final
