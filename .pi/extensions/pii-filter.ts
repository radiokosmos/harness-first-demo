// pi adapter for the PII hooks (pii/hooks.mjs) — keep customer PII away from the model.
//
//   tool_result              echelon 1    PII_FILTER          (default on)
//   before_provider_request  echelon 2    PII_PROVIDER_GUARD  (default off)
//   tool_call                way back     PII_DETOKENIZE      (default off)
//
// PII_PAYLOAD_LOG=<file> appends every request as it actually leaves (after masking).
// Behaviour lives in pii/hooks.mjs; this file only plugs it into pi.
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFileSync } from "node:fs";
import { PiiMasker } from "../../pii/masker.mjs";
import { onToolResult, onProviderRequest, onToolCall } from "../../pii/hooks.mjs";
import { emit } from "../../hooks/events.mjs";

const masker = new PiiMasker(); // one per session: the same value keeps the same token
const flag = (name: string, dflt: string) => (process.env[name] ?? dflt) !== "0";
const line = (s: Record<string, number>) => Object.entries(s).map(([k, v]) => `${k}×${v}`).join(", ");

export default function (pi: ExtensionAPI) {
  const warn = (ctx: any, msg: string, kind = "masked") => {
    ctx?.ui?.notify?.(msg, "warning");
    console.error(`[pii-filter] ${msg}`);
    emit("pii-filter", kind, msg); // act 4: unattended runs read events, not stderr
  };

  pi.on("tool_call", async (event) => {
    if (!flag("PII_DETOKENIZE", "0")) return;
    const input = event.input as { command?: string };
    if (typeof input.command === "string") input.command = onToolCall(masker, event.toolName, input.command);
  });

  pi.on("tool_result", async (event, ctx) => {
    if (!flag("PII_FILTER", "1")) return;
    const agg: Record<string, number> = {};
    let changed = false;
    const content = event.content.map((item: any) => {
      if (item?.type !== "text") return item;
      const r = onToolResult(masker, event.toolName, item.text);
      if (r.text === item.text) return item;
      changed = true;
      for (const [k, v] of Object.entries(r.stats)) agg[k] = (agg[k] ?? 0) + (v as number);
      return { ...item, text: r.text };
    });
    if (!changed) return;
    warn(ctx, `masked ${line(agg)} in a ${event.toolName} result`);
    return { content };
  });

  pi.on("before_provider_request", (event, ctx) => {
    let payload = event.payload;
    if (flag("PII_FILTER", "1") && flag("PII_PROVIDER_GUARD", "0")) {
      const r = onProviderRequest(masker, event.payload);
      payload = r.payload;
      if (Object.keys(r.stats).length) {
        warn(ctx, `provider guard masked ${line(r.stats)} in the outgoing request — PII reached the context outside a tool result`, "provider-guard");
      }
    }
    const log = process.env.PII_PAYLOAD_LOG;
    if (log) appendFileSync(log, JSON.stringify(payload) + "\n");
    return payload === event.payload ? undefined : payload;
  });
}
