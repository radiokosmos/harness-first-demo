# models/staging/

- `stg_events` has duplicates from mobile replays; dedupe on `event_id` (keep the earliest `ingested_at`).
