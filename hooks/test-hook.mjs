// bin/test-hook — table-driven cases for isProdRun.
import { isProdRun } from "./core.mjs";

const cases = [
  ["dbt build --target prod", true],
  ["dbt run -t prod -s fct_activity_daily", true],
  ["DBT_TARGET=prod dbt build", true],
  ["dbt build --target=prod", true],
  ["DBT_PROFILES_DIR=. .venv/bin/dbt build --target prod -s fct_activity_daily", true],
  ["dbt seed && dbt build --target prod", true],
  ["dbt build --target dev", false],
  ['grep -- "--target prod" AGENTS.md', false],
  ['git commit -m "block --target prod in hook"', false],
];

let failed = 0;
for (const [cmd, expected] of cases) {
  let got;
  try { got = isProdRun(cmd); } catch (e) { got = `throws: ${e.message}`; }
  const ok = got === expected;
  failed += !ok;
  const want = expected ? "block" : "allow";
  const mark = ok ? "\x1b[32m✓\x1b[0m" : "\x1b[31m✗\x1b[0m";
  console.log(`${mark} ${want.padEnd(5)}  ${cmd}${ok ? "" : `   \x1b[31m(got ${got === true ? "block" : got === false ? "allow" : got})\x1b[0m`}`);
}
console.log(`\n${failed ? "\x1b[31m" : "\x1b[32m"}${cases.length - failed} of ${cases.length}\x1b[0m`);
process.exit(failed ? 1 : 0);
