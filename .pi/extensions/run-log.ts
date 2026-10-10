// Structured log of an unattended run: every tool call and whether it worked.
// Active only when RUN_DIR is set (bin/run-headless). Feeds ci/verify-run.mjs.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFileSync } from "node:fs";
import { join } from "node:path";

const ERROR_TEXT = /IO Error|Catalog Error|could not open|Is a directory|No such file|Permission denied|Traceback|ERROR|command not found/i;

export default function (pi: ExtensionAPI) {
  const dir = process.env.RUN_DIR;
  if (!dir) return;
  const log = (o: object) => appendFileSync(join(dir, "log.jsonl"), JSON.stringify({ t: new Date().toISOString(), ...o }) + "\n");

  pi.on("tool_call", async (event) => {
    log({ event: "tool_call", id: (event as any).toolCallId, tool: event.toolName, command: (event.input as any)?.command ?? (event.input as any)?.path ?? null });
  });

  pi.on("tool_result", async (event) => {
    const text = event.content.map((c: any) => (c?.type === "text" ? c.text : "")).join("\n");
    log({ event: "tool_result", id: (event as any).toolCallId, tool: event.toolName, isError: Boolean(event.isError) || ERROR_TEXT.test(text), head: text.slice(0, 300) });
  });
}
