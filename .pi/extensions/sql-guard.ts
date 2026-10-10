// pi adapter for the day-boundary guard: after the agent writes or edits a model,
// append the guard's findings to the tool result — the agent reads them right away.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { readFileSync } from "node:fs";
import { findBareDayCasts, ADVICE } from "../../guards/day-boundary.mjs";
import { emit } from "../../hooks/events.mjs";

export default function (pi: ExtensionAPI) {
  pi.on("tool_result", async (event) => {
    if (event.toolName !== "write" && event.toolName !== "edit") return;
    const path = (event.input as { path?: string })?.path ?? "";
    if (!/models\/.*\.sql$/.test(path)) return;
    let hits;
    try { hits = findBareDayCasts(readFileSync(path, "utf8")); } catch { return; }
    if (!hits.length) return;
    const msg = `[sql-guard] ${path}: ${hits.map((h) => `line ${h.line}: ${h.text.trim()}`).join("; ")} — ${ADVICE}`;
    console.error(msg);
    emit("sql-guard", "day-boundary", msg);
    return { content: [...event.content, { type: "text" as const, text: "\n" + msg }] };
  });
}
