// Day-boundary guard — promoted from reflections (class edge-case, seen twice):
// event timestamps are UTC, the warehouse session is not, so "the date of a
// timestamp" must say which time zone it means.
//
// Used by bin/lint-models (any runtime, CI) and .pi/extensions/sql-guard.ts.

/** Strip SQL and Jinja comments: a comment saying "UTC" is not UTC handling. */
export function stripComments(sql) {
  return sql.replace(/\{#[\s\S]*?#\}/g, "").replace(/\/\*[\s\S]*?\*\//g, "").replace(/--[^\n]*/g, "");
}

/**
 * Find places where SQL takes the date of a timestamp in the session time zone.
 * Returns [{ line, text }] — empty when the SQL is fine.
 *
 * Must flag:   cast(event_ts as date) · event_ts::date · date_trunc('day', event_ts)
 *              current_date (bare) · date(event_ts)
 * Must allow:  cast(timezone('UTC', event_ts) as date) · (event_ts at time zone 'UTC')::date
 */
export function findBareDayCasts(sql) {
  // TODO: act 5, exercise 5a
  return [];
}

export const ADVICE =
  "event timestamps are UTC and the session time zone is not — take the date of timezone('UTC', <ts>), never of the bare timestamp.";
