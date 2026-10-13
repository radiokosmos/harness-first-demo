// PII hooks for the agent loop. The masker (pii/masker.mjs) is done.

export const SQL_TOOLS = /\bduckdb\b|\bdbt\s+show\b/;

/** Mask every string inside a JSON-like value; counts hits by type into `stats`. (ready) */
export function maskDeep(value, masker, stats = {}) {
  if (typeof value === "string") {
    const r = masker.mask(value);
    for (const [k, v] of Object.entries(r.stats)) stats[k] = (stats[k] ?? 0) + v;
    return r.text;
  }
  if (Array.isArray(value)) return value.map((v) => maskDeep(v, masker, stats));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, maskDeep(v, masker, stats)]));
  }
  return value;
}

/** After a tool runs, before the model sees its output. Returns { text, stats }. */
export function onToolResult(masker, toolName, text) {
  // TODO: act 3, exercise 3
  return { text, stats: {} };
}

/** The outgoing request to the model provider. Returns { payload, stats }. */
export function onProviderRequest(masker, payload) {
  // TODO: act 3, exercise 3
  return { payload, stats: {} };
}

/** Before a tool runs: lets the model use a token like <EMAIL_3> in a query. Returns the command. */
export function onToolCall(masker, toolName, command) {
  // TODO: act 3, exercise 3
  return command;
}
