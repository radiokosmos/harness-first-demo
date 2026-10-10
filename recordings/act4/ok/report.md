## Nightly report — `fct_activity_daily`

**Build:** ✅ succeeded. `dbt build -s fct_activity_daily` created the table and all 4 schema tests (`unique`/`not_null` on `activity_date`, `not_null` on `active_users`/`event_count`) passed.

**`bin/data-diff fct_activity_daily`:** ❌ **FAIL**

| check | result |
|---|---|
| completeness | 1 of 15 days within 0.5% |
| keys | 2 of 15 days within 0.5% |
| nulls | pass (1 of 1) |

### Problem found

The model buckets events by day using a bare `cast(event_ts as date)`, which gets evaluated in the active **session timezone**. `profiles.yml` sets the dev connection's `TimeZone` to `America/Los_Angeles`, but `event_ts` is stored in UTC (per team convention). So the cast silently shifts each event ~7–8 hours earlier before taking the date, moving roughly 650–750 events/night into the previous calendar day.

Effects, confirmed directly against `raw.raw_events`:
- Every real day except 10-06 is off by 1–5% on `event_count`/`active_users` (too low some days, too high others, since each day gains late-night spillover from the next day and loses its own late-night events to the day before).
- A spurious extra bucket, `2026-09-30`, shows up in the model (684 events / 550 users) with no corresponding source day — it's just the UTC-10-01 early-morning events shifted a day back by the PST cast.

Root cause: the mart doesn't convert explicitly to UTC before taking the date (unlike the comment in `bin/data-diff`'s source SQL, which does `timezone('UTC', event_ts)` precisely because of this). Fix would be to change `cast(event_ts as date)` to `cast(timezone('UTC', event_ts) as date)` in `models/marts/fct_activity_daily.sql` — did not apply it, flagging for review per the ask (build + diff + report only).

No PII, no seed, no test-count issues otherwise.
