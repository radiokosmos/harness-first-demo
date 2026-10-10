// pi adapter for the PII masker — keep customer PII out of the LLM context.
//
//   echelon 1  tool_result              mask what tools return, before the model sees it   (PII_FILTER, default on)
//   echelon 2  before_provider_request  mask the outgoing request — the smoke detector     (PII_PROVIDER_GUARD, default off)
//   back       tool_call                tokens -> real values, only for SQL commands       (PII_DETOKENIZE, default off)
//
// PII_PAYLOAD_LOG=<file> appends every request as it actually leaves (after masking).
// Warnings go to the UI *and* stderr, so headless runs keep them (act 4).
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFileSync } from "node:fs";
import { PiiMasker } from "../../pii/masker.mjs";

const masker = new PiiMasker(); // one per session: the same value keeps the same token
const flag = (name: string, dflt: string) => (process.env[name] ?? dflt) !== "0";
const SQL_TOOLS = /\bduckdb\b|\bdbt\s+show\b/;

type Stats = Record<string, number>;
const add = (agg: Stats, s: Stats) => { for (const [k, v] of Object.entries(s)) agg[k] = (agg[k] ?? 0) + v; };
const line = (s: Stats) => Object.entries(s).map(([k, v]) => `${k}×${v}`).join(", ");

function maskDeep(value: unknown, agg: Stats): unknown {
  if (typeof value === "string") { const r = masker.mask(value); add(agg, r.stats); return r.text; }
  if (Array.isArray(value)) return value.map((v) => maskDeep(v, agg));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, maskDeep(v, agg)]));
  }
  return value;
}

export default function (pi: ExtensionAPI) {
  const warn = (ctx: any, msg: string) => {
    ctx?.ui?.notify?.(msg, "warning");
    console.error(`[pii-filter] ${msg}`);
  };

  pi.on("tool_call", async (event) => {
    if (!flag("PII_DETOKENIZE", "0") || event.toolName !== "bash") return;
    const input = event.input as { command?: string };
    if (input.command && SQL_TOOLS.test(input.command)) input.command = masker.detokenize(input.command);
  });

  pi.on("tool_result", async (event, ctx) => {
    if (!flag("PII_FILTER", "1")) return;
    const agg: Stats = {};
    let changed = false;
    const content = event.content.map((item: any) => {
      if (item?.type !== "text") return item;
      const r = masker.mask(item.text);
      if (!Object.keys(r.stats).length) return item;
      changed = true; add(agg, r.stats);
      return { ...item, text: r.text };
    });
    if (!changed) return;
    warn(ctx, `masked ${line(agg)} in a ${event.toolName} result`);
    return { content };
  });

  pi.on("before_provider_request", (event, ctx) => {
    let payload = event.payload;
    if (flag("PII_FILTER", "1") && flag("PII_PROVIDER_GUARD", "0")) {
      const agg: Stats = {};
      payload = maskDeep(event.payload, agg) as typeof event.payload;
      if (Object.keys(agg).length) {
        warn(ctx, `provider guard masked ${line(agg)} in the outgoing request — PII reached the context outside a tool result`);
      }
    }
    const log = process.env.PII_PAYLOAD_LOG;
    if (log) appendFileSync(log, JSON.stringify(payload) + "\n");
    return payload === event.payload ? undefined : payload;
  });
}
