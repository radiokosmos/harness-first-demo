// bin/test-guard — cases for findBareDayCasts.
import { findBareDayCasts } from "./day-boundary.mjs";

const cases = [
  ["select cast(event_ts as date) as d from e", true],
  ["select event_ts::date from e", true],
  ["select date_trunc('day', event_ts) from e", true],
  ["select * from e where d = current_date - 1", true],
  ["select date(event_ts) from e", true],
  ["select cast(timezone('UTC', event_ts) as date) as d from e", false],
];
let failed = 0;
for (const [sql, bad] of cases) {
  const got = findBareDayCasts(sql).length > 0;
  const ok = got === bad;
  failed += !ok;
  console.log(`${ok ? "\x1b[32m✓" : "\x1b[31m✗"}\x1b[0m ${bad ? "flag " : "allow"}  ${sql.replace(/\n/g, " ⏎ ")}`);
}
console.log(`\n${failed ? "\x1b[31m" : "\x1b[32m"}${cases.length - failed} of ${cases.length}\x1b[0m`);
process.exit(failed ? 1 : 0);
