// Where the PII masker sits in an agent loop — one core for every runtime.
// Adapters: .pi/extensions/pii-filter.ts (pi). bin/replay-session and
// bin/test-pii-hooks use the same functions.
//
// The masker (pii/masker.mjs) is done. The question here is not how to find
// an email, but WHERE to stand so that none reaches the model provider.

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

/**
 * Echelon 1 — after a tool runs, before the model sees its output.
 * Returns { text, stats }. Every tool, not just SQL: a file read or a grep
 * over a CSV returns customer data too.
 */
export function onToolResult(masker, toolName, text) {
  return masker.mask(text);
}

/**
 * Echelon 2 — the last line: the whole outgoing request to the provider.
 * Catches what reached the context some other way. Returns { payload, stats };
 * every hit here is something echelon 1 missed.
 */
export function onProviderRequest(masker, payload) {
  const stats = {};
  return { payload: maskDeep(payload, masker, stats), stats };
}

/**
 * The way back — just before a tool runs: let a SQL command use a token like
 * <EMAIL_3> by swapping in the real value. Only for SQL tools: anything else
 * (curl, writing a file) would be an exfiltration path. Returns the command.
 * A SQL command chained with a network call (`duckdb … && curl -d "to=<EMAIL_1>" …`)
 * is not "just SQL": the agent's version detokenized it; the case is pinned in
 * pii/test-hooks.mjs.
 */
export function onToolCall(masker, toolName, command) {
  if (toolName !== "bash" || !SQL_TOOLS.test(command)) return command;
  if (/\b(curl|wget|nc|ssh)\b/.test(command)) return command; // SQL plus a network call is not "just SQL"
  return masker.detokenize(command);
}
