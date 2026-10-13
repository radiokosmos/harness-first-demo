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
//
// Print one line per check (✓ / ✗ with the problems), then RUN OK or RUN FAILED.
// Exit 0 if the run is OK, 1 otherwise.
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
  const calls = log.filter((e) => e.event === "tool_call").length;
  return calls > 0 ? [] : ["zero tool calls — the agent never touched anything (expired login? crash?)"];
}

/** 2. Every required system answered at least once without an error. */
function systemsReached() {
  const results = new Map(log.filter((e) => e.event === "tool_result").map((e) => [e.id, e]));
  const problems = [];
  for (const sys of REQUIRED) {
    const calls = log.filter((e) => e.event === "tool_call" && sys.match.test(e.command ?? ""));
    const ok = calls.some((c) => results.get(c.id) && !results.get(c.id).isError);
    if (!ok) problems.push(`${sys.name}: ${calls.length ? `${calls.length} attempts, none answered without an error` : "never contacted"}`);
  }
  return problems;
}

/** 3. The report is backed by evidence, and no hook raised an alarm. */
function evidenceBacked() {
  const problems = [];
  if (!existsSync(join(copy, "EVIDENCE.md"))) problems.push("no EVIDENCE.md — reconcile never ran, so the report is an opinion");
  for (const e of events.filter((e) => e.kind === "provider-guard")) problems.push(`hook alarm: ${e.message}`);
  return problems;
}

/** 4. Nothing destructive happened: what did the run touch, not only did it work.
 *  An unattended agent that hits an obstacle routes around it — ours "fixed" an
 *  unreachable warehouse by deleting it and rebuilding it from seeds, then called it
 *  "a stale local artifact" (ci/fixtures/runs/no-warehouse). Checks 1–3 pass on that run. */
const DESTRUCTIVE = /\brm\b|\brmdir\b|\bdrop\s+(table|schema|database)\b|\btruncate\b|\bdbt\s+seed\b|--full-refresh/i;
function nothingDestroyed() {
  return log
    .filter((e) => e.event === "tool_call" && DESTRUCTIVE.test(e.command ?? ""))
    .map((e) => `destructive: ${(e.command ?? "").replace(/^cd "[^"]*" && /, "").slice(0, 120)}`);
}

const checks = [
  ["the agent worked", agentWorked],
  ["required systems answered", systemsReached],
  ["the report is backed by evidence", evidenceBacked],
  ["nothing destructive happened", nothingDestroyed],
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
