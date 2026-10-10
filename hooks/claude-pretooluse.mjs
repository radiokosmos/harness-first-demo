// Claude Code adapter: PreToolUse hook for Bash. Exit 2 blocks the call and
// shows stderr to the model. Fail-closed: if the check itself breaks, block.
import { isProdRun, REASON } from "./core.mjs";

let raw = "";
process.stdin.on("data", (c) => (raw += c));
process.stdin.on("end", () => {
  try {
    const event = JSON.parse(raw || "{}");
    const command = event?.tool_input?.command ?? "";
    if (isProdRun(command)) {
      process.stderr.write(REASON + "\n");
      process.exit(2);
    }
    process.exit(0);
  } catch (err) {
    process.stderr.write(`prod guardrail failed (${err.message}) — blocking to be safe\n`);
    process.exit(2);
  }
});
