// Act 4: did an unattended run actually do its job? Decided by artifacts,
// never by the agent's report and never by the exit code.
//
//   node ci/verify-run.mjs <run dir>        (bin/verify-run)
//
// A run dir from bin/run-headless has:
//   log.jsonl     {event: "tool_call"|"tool_result", id, tool, command?, isError?, head?}
//   events.jsonl  {source, kind, message} from hooks (pii-filter, block-prod)
//   report.md     what the agent "reported"
//   nightly/      the agent's working copy
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

const run = process.argv[2];
if (!run || !existsSync(run)) {
  console.error("usage: bin/verify-run <run dir>");
  process.exit(2);
}
const jsonl = (f) => (existsSync(join(run, f)) ? readFileSync(join(run, f), "utf8").trim().split("\n").filter(Boolean).map(JSON.parse) : []);
const log = jsonl("log.jsonl");
const events = jsonl("events.jsonl");
const copy = join(run, "nightly");

// Systems the nightly job must reach. A run that never got an answer from
// one of them can't have checked anything there.
const REQUIRED = [{ name: "warehouse", match: /duckdb|\bdbt\b|data-diff|reconcile|check-counts/ }];

/** 1. The agent worked: it made at least one tool call. */
function agentWorked() {
  // TODO: act 4, exercise 4a — return [] if fine, or a list of problems.
  return [];
}

/** 2. Every required system answered at least once without an error. */
function systemsReached() {
  // TODO: act 4, exercise 4a — pair tool_call and tool_result by id; a system is
  // reached if some call whose command matches it has a result with isError false.
  return [];
}

/** 3. (worked example) The report is backed by evidence, and no hook raised an alarm. */
function evidenceBacked() {
  const problems = [];
  if (!existsSync(join(copy, "EVIDENCE.md"))) problems.push("no EVIDENCE.md — reconcile never ran, so the report is an opinion");
  for (const e of events.filter((e) => e.kind === "provider-guard")) problems.push(`hook alarm: ${e.message}`);
  return problems;
}

const checks = [
  ["the agent worked", agentWorked],
  ["required systems answered", systemsReached],
  ["the report is backed by evidence", evidenceBacked],
];

let failed = 0;
for (const [title, fn] of checks) {
  const problems = fn();
  if (problems.length) {
    failed++;
    console.log(`\x1b[31m✗ ${title}\x1b[0m`);
    for (const p of problems) console.log(`    \x1b[2m${p}\x1b[0m`);
  } else console.log(`\x1b[32m✓ ${title}\x1b[0m`);
}
console.log(failed ? `\n\x1b[31mRUN FAILED\x1b[0m — whatever report.md says` : `\n\x1b[32mRUN OK\x1b[0m`);
process.exit(failed ? 1 : 0);
