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

    -- mobile replays share event_id; keep the earliest ingested_at
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
        date_trunc('day', event_ts) as event_date,
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
    from daily
    group by event_date

)

select * from final
