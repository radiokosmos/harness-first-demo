with source as (

    select
        event_id,
        user_id,
        event_type,
        platform,
        event_ts,
        ingested_at
    from {{ source('raw', 'raw_events') }}

),

deduped as (

    select
        *,
        row_number() over (
            partition by event_id order by ingested_at asc
        ) as rn
    from source

)

select
    event_id,
    user_id,
    event_type,
    platform,
    event_ts,
    ingested_at
from deduped
where rn = 1
