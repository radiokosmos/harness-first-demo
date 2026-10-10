// Hook events for unattended runs. A warning a human would read in the UI
// is written to $RUN_DIR/events.jsonl instead — nobody reads stderr at 3 a.m.
import { appendFileSync } from "node:fs";
import { join } from "node:path";

export function emit(source, kind, message, data = {}) {
  const dir = process.env.RUN_DIR;
  if (!dir) return;
  const line = { t: new Date().toISOString(), source, kind, message, ...data };
  appendFileSync(join(dir, "events.jsonl"), JSON.stringify(line) + "\n");
}
