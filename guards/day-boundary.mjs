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
 * Find where SQL takes the date of a timestamp in the session time zone.
 * Returns [{ line, text }], empty when fine.
 *
 * Comments are stripped first. Then each line is checked: cast(… as date), ::date,
 * date_trunc('day', …), date(…) and current_date are hits, unless the line says
 * which time zone it means — timezone('UTC', …) or at time zone 'UTC'.
 */
const UTC = /timezone\s*\(\s*'utc'|at\s+time\s+zone\s+'utc'|convert_timezone/i;
const PATTERNS = [
  /cast\s*\(\s*([\w."]+)\s+as\s+date\s*\)/gi,  // cast(event_ts as date)
  /([\w."]+)\s*::\s*date\b/gi,                       // event_ts::date
  /date_trunc\s*\(\s*'day'\s*,\s*([\w."]+)\s*\)/gi, // date_trunc('day', event_ts)
  /\bdate\s*\(\s*([\w."]+)\s*\)/gi,                 // date(event_ts)
  /\bcurrent_date\b/gi,                                // "today" in the session time zone
];

export function findBareDayCasts(sql) {
  const hits = [];
  stripComments(sql).split("\n").forEach((text, i) => {
    if (UTC.test(text)) return; // this line says which time zone it means
    if (PATTERNS.some((rx) => { rx.lastIndex = 0; return rx.test(text); })) hits.push({ line: i + 1, text });
  });
  return hits;
}

export const ADVICE =
  "event timestamps are UTC and the session time zone is not — take the date of timezone('UTC', <ts>), never of the bare timestamp.";
