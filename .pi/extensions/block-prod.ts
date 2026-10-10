// pi adapter for the prod guardrail. Fail-closed: if the check breaks, block.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { isProdRun, REASON } from "../../hooks/core.mjs";
import { emit } from "../../hooks/events.mjs";

export default function (pi: ExtensionAPI) {
  pi.on("tool_call", async (event) => {
    if (event.toolName !== "bash") return;
    const command = (event.input as { command?: string })?.command ?? "";
    try {
      if (isProdRun(command)) {
        emit("block-prod", "blocked", REASON, { command });
        return { block: true, reason: REASON };
      }
    } catch (err) {
      return { block: true, reason: `prod guardrail failed (${(err as Error).message}) — blocking to be safe` };
    }
  });
}
