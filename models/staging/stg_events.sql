select
    event_id,
    user_id,
    event_type,
    platform,
    event_ts,
    ingested_at
from {{ source('raw', 'raw_events') }}
