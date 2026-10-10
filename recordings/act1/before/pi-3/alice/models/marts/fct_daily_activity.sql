-- grain: one row per day (event_date)

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
        event_ts,
        row_number() over (
            partition by event_id
            order by ingested_at asc
        ) as rn
    from events

),

daily as (

    select
        cast(event_ts as date) as event_date,
        count(distinct user_id) as active_users,
        count(*) as event_count
    from deduped
    where rn = 1
    group by cast(event_ts as date)

),

final as (

    select
        event_date,
        active_users,
        event_count
    from daily

)

select * from final
