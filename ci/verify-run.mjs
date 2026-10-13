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
import { existsSync } from "node:fs";

const run = process.argv[2];
if (!run || !existsSync(run)) {
  console.error("usage: bin/verify-run <run dir>");
  process.exit(2);
}

// TODO: act 4, exercise 4 — write the checks.
console.log("RUN OK");
process.exit(0);
