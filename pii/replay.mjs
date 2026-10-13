// bin/replay-session — what would a recorded agent session send to the model
// provider, given the hooks in pii/hooks.mjs as they are right now?
//
//   bin/replay-session sessions/complaints-with-paste.jsonl
//
// Replays the last recorded request (it carries the whole conversation) through
// onToolResult / onProviderRequest / onToolCall and counts the PII that would
// still leave the machine, by the path it took. No agent, no network: seconds.
//
// One assumption: once tool results are masked, the model only ever saw tokens,
// so its own text is replayed with the same tokens.
import { readFileSync } from "node:fs";
import { PiiMasker, luhnValid, ibanValid } from "./masker.mjs";
import { onToolResult, onProviderRequest, onToolCall, SQL_TOOLS } from "./hooks.mjs";

const file = process.argv[2];
if (!file) { console.error("usage: bin/replay-session <session.jsonl>"); process.exit(2); }
const lines = readFileSync(file, "utf8").trim().split("\n");
const request = JSON.parse(lines.at(-1));

// independent of the masker: what a reviewer would count as PII in the request
const DETECT = {
  EMAIL: [/[A-Za-z0-9._%+-]+@(?!corp\.example)[A-Za-z0-9.-]+\.[A-Za-z]{2,}/g, () => true],
  PHONE: [/\+\d[\d\s\-().]{7,}\d/g, (m) => m.replace(/\D/g, "").length >= 9],
  IBAN: [/\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b/g, (m) => ibanValid(m)],
  CARD: [/\b(?:\d[ -]?){14,18}\d\b/g, (m) => luhnValid(m.replace(/[ -]/g, ""))],
};
const TYPES = Object.keys(DETECT);
const PATHS = ["tool results", "user messages", "model's own text"];
const found = () => Object.fromEntries(PATHS.map((p) => [p, Object.fromEntries(TYPES.map((t) => [t, new Set()]))]));
function scan(text, path, into) {
  for (const [t, [rx, ok]] of Object.entries(DETECT)) for (const m of text.matchAll(rx)) if (ok(m[0])) into[path][t].add(m[0].replace(/\W/g, "").toLowerCase());
}

// which hooks do something yet?
const probe = new PiiMasker();
const status = {
  onToolResult: onToolResult(new PiiMasker(), "bash", "x@example.org").text !== "x@example.org",
  onProviderRequest: JSON.stringify(onProviderRequest(new PiiMasker(), { t: "x@example.org" }).payload) !== JSON.stringify({ t: "x@example.org" }),
  onToolCall: (probe.mask("x@example.org"), onToolCall(probe, "bash", `duckdb x "select '<EMAIL_1>'"`).includes("x@example.org")),
};

const masker = new PiiMasker();
let resultsMasked = false;
const detok = [];
const messages = request.messages.map((m) => ({
  ...m,
  content: !Array.isArray(m.content) ? m.content : m.content.map((c) => {
    if (c.type === "tool_result") {
      const raw = Array.isArray(c.content) ? c.content.map((x) => x.text ?? "").join("\n") : String(c.content ?? "");
      const r = onToolResult(masker, "bash", raw);
      if (r.text !== raw) resultsMasked = true;
      return { ...c, content: [{ type: "text", text: r.text }], _path: "tool results" };
    }
    if (c.type === "tool_use") {
      const cmd = c.input?.command ?? "";
      const text = resultsMasked ? masker.mask(cmd).text : cmd;
      const run = onToolCall(masker, "bash", text);
      if (run !== text) detok.push({ wrote: text, ran: run });
      return { ...c, input: { ...c.input, command: text }, _path: "model's own text" };
    }
    if (c.type === "text") {
      const text = m.role === "assistant" && resultsMasked ? masker.mask(c.text).text : c.text;
      return { ...c, text, _path: m.role === "assistant" ? "model's own text" : "user messages" };
    }
    return c;
  }),
}));

const before = found();
for (const m of messages) for (const c of Array.isArray(m.content) ? m.content : []) if (c._path) scan(JSON.stringify(c), c._path, before);
const guard = onProviderRequest(masker, { ...request, messages });
const after = found();
for (const m of guard.payload.messages ?? []) for (const c of Array.isArray(m.content) ? m.content : []) if (c._path) scan(JSON.stringify(c), c._path, after);

const G = "\x1b[32m", R = "\x1b[31m", D = "\x1b[2m", B = "\x1b[1m", X = "\x1b[0m";
console.log(`${D}${file} · replaying the last recorded request (${request.messages.length} messages)${X}\n`);
console.log("hooks   " + Object.entries(status).map(([k, v]) => `${v ? G + "✓" : D + "·"} ${k}${X}`).join("   ") + `\n`);
console.log(`${B}would leave the machine, by path${X}        ${TYPES.map((t) => t.padStart(6)).join("")}`);
let total = 0;
for (const p of PATHS) {
  const n = TYPES.map((t) => after[p][t].size);
  total += n.reduce((a, b) => a + b, 0);
  console.log(`  ${p.padEnd(37)}${n.map((x) => (x ? R : G) + String(x).padStart(6) + X).join("")}`);
}
const caught = PATHS.map((p) => [p, TYPES.reduce((a, t) => a + before[p][t].size - after[p][t].size, 0)]).filter(([, n]) => n);
console.log();
if (caught.length) console.log(`provider guard masked: ${caught.map(([p, n]) => `${n} in ${p}`).join(", ")} ${D}— what echelon 1 missed${X}`);
if (detok.length) console.log(`detokenized ${detok.length} SQL command(s) for execution; the model still only wrote tokens`);
console.log(total ? `${R}${total} distinct PII values would reach the provider.${X}` : `${G}No PII values would reach the provider.${X}`);
