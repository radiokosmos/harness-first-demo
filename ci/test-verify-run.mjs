// bin/test-verify-run — table-driven cases for ci/verify-run.mjs:
// a recorded nightly run (ci/fixtures/runs/<name>) and the verdict it must get.
import { spawnSync } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const fixtures = join(here, "fixtures", "runs");

const cases = [
  ["ok", "RUN OK"], // found the real day-boundary bug
  ["expired-token", "RUN FAILED"], // login expired: nothing on stdout, exit 0, "nothing needs attention"
  // found after the agent's checks passed both: this run worked, reached the warehouse and brought
  // evidence — after `rmdir demo.duckdb && dbt seed`. Ask what a run touched, not only whether it worked.
  ["no-warehouse", "RUN FAILED"],
];

let failed = 0;
for (const [name, expected] of cases) {
  const r = spawnSync(process.execPath, [join(here, "verify-run.mjs"), join(fixtures, name)], { encoding: "utf8" });
  const out = `${r.stdout ?? ""}${r.stderr ?? ""}`.replace(/\x1b\[[0-9;]*m/g, "");
  const said = /RUN FAILED/.test(out) ? "RUN FAILED" : /RUN OK/.test(out) ? "RUN OK" : "no verdict";
  const got = said === "no verdict" || r.status === (said === "RUN OK" ? 0 : 1) ? said : `${said}, exit ${r.status}`;
  const ok = got === expected;
  failed += !ok;
  const mark = ok ? "\x1b[32m✓\x1b[0m" : "\x1b[31m✗\x1b[0m";
  console.log(`${mark} ${expected.padEnd(10)}  ${name}${ok ? "" : `   \x1b[31m(got ${got})\x1b[0m`}`);
}
console.log(`\n${failed ? "\x1b[31m" : "\x1b[32m"}${cases.length - failed} of ${cases.length}\x1b[0m`);
process.exit(failed ? 1 : 0);
