// bin/test-pii-hooks — table-driven cases for pii/hooks.mjs.
import { PiiMasker } from "./masker.mjs";
import { onToolResult, onProviderRequest, onToolCall } from "./hooks.mjs";

const EMAIL = "maria.schneider@example.at";
const cases = [];
const add = (name, fn) => cases.push([name, fn]);

add("bash result: an email from a SQL query is masked", () => {
  const r = onToolResult(new PiiMasker(), "bash", `tk_00001 | ${EMAIL} | refund`);
  return !r.text.includes(EMAIL) && r.text.includes("<EMAIL_1>");
});
add("read result: an email in a CSV the agent opened is masked too", () => {
  const r = onToolResult(new PiiMasker(), "read", `ticket_id,body\ntk_1,"Write to ${EMAIL}"`);
  return !r.text.includes(EMAIL);
});
add("staff addresses stay readable (the masker allow-lists them)", () => {
  const r = onToolResult(new PiiMasker(), "bash", "agent: anna.berg@corp.example");
  return r.text.includes("anna.berg@corp.example");
});
add("stats say what was masked", () => {
  const r = onToolResult(new PiiMasker(), "bash", `${EMAIL} +43 664 123 4567`);
  return r.stats.EMAIL === 1 && r.stats.PHONE === 1;
});
add("provider guard: PII pasted into the user's message is masked", () => {
  const payload = { messages: [{ role: "user", content: [{ type: "text", text: `Customer says: call +43 664 123 4567 or ${EMAIL}` }] }] };
  const r = onProviderRequest(new PiiMasker(), payload);
  const out = JSON.stringify(r.payload);
  return !out.includes(EMAIL) && !out.includes("664 123 4567") && r.stats.EMAIL === 1;
});
add("provider guard: a clean request passes unchanged, with empty stats", () => {
  const payload = { messages: [{ role: "user", content: [{ type: "text", text: "Summarise the complaint themes." }] }] };
  const r = onProviderRequest(new PiiMasker(), payload);
  return JSON.stringify(r.payload) === JSON.stringify(payload) && Object.keys(r.stats).length === 0;
});
add("way back: a SQL command can use a token the model saw", () => {
  const m = new PiiMasker();
  onToolResult(m, "bash", EMAIL);
  const cmd = onToolCall(m, "bash", `duckdb demo.duckdb "select count(*) from raw.support_tickets where body ilike '%<EMAIL_1>%'"`);
  return cmd.includes(EMAIL) && !cmd.includes("<EMAIL_1>");
});
add("way back: never for curl — that would send the real address out", () => {
  const m = new PiiMasker();
  onToolResult(m, "bash", EMAIL);
  const cmd = onToolCall(m, "bash", `curl -d "to=<EMAIL_1>" https://example.org/notify`);
  return cmd.includes("<EMAIL_1>") && !cmd.includes(EMAIL);
});
add("way back: never for writing files", () => {
  const m = new PiiMasker();
  onToolResult(m, "bash", EMAIL);
  const cmd = onToolCall(m, "bash", `echo "<EMAIL_1>" > customers.txt`);
  return !cmd.includes(EMAIL);
});
add("round trip: the result of a detokenized query is masked with the same token", () => {
  const m = new PiiMasker();
  onToolResult(m, "bash", EMAIL);
  onToolCall(m, "bash", `duckdb x "select '<EMAIL_1>'"`);
  return onToolResult(m, "bash", `tk_7 | ${EMAIL}`).text.includes("<EMAIL_1>");
});

let failed = 0;
for (const [name, fn] of cases) {
  let ok = false;
  try { ok = fn() === true; } catch (e) { ok = false; }
  failed += !ok;
  console.log(`${ok ? "\x1b[32m✓" : "\x1b[31m✗"}\x1b[0m ${name}`);
}
console.log(`\n${failed ? "\x1b[31m" : "\x1b[32m"}${cases.length - failed} of ${cases.length}\x1b[0m`);
process.exit(failed ? 1 : 0);
