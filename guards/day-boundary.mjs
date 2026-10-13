// Day-boundary guard — promoted from reflections (class edge-case, seen twice):
// event timestamps are UTC, the warehouse session is not, so "the date of a
// timestamp" must say which time zone it means.
//
// Used by bin/lint-models (any runtime, CI) and .pi/extensions/sql-guard.ts.

/** Find where SQL takes the date of a timestamp in the session time zone. Returns [{ line, text }], empty when fine. */
export function findBareDayCasts(sql) {
  // TODO: act 5, exercise 5a
  return [];
}

export const ADVICE =
  "event timestamps are UTC and the session time zone is not — take the date of timezone('UTC', <ts>), never of the bare timestamp.";
