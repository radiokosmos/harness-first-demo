// bin/pii-score — how good is pii/masker.mjs on a labelled corpus?
//   bin/pii-score            public corpus (tune on this)
//   bin/pii-score --hidden   hidden corpus (the leaderboard)
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { PiiMasker, TYPES } from "./masker.mjs";

const hidden = process.argv.includes("--hidden");
const file = new URL(`../corpus/${hidden ? "hidden.jsonl.gz" : "public.jsonl"}`, import.meta.url);
const raw = hidden ? gunzipSync(readFileSync(file)).toString() : readFileSync(file, "utf8");
const docs = raw.trim().split("\n").map((l) => JSON.parse(l));

const per = Object.fromEntries(TYPES.map((t) => [t, { total: 0, caught: 0 }]));
let tokens = 0, caughtAll = 0;
const missed = [], falsePos = [];

for (const doc of docs) {
  const masker = new PiiMasker();
  const { text } = masker.mask(doc.text);
  const n = (text.match(/<[A-Z]+_\d+>/g) ?? []).length;
  tokens += n;
  let caught = 0;
  for (const s of doc.spans) {
    const value = doc.text.slice(s.start, s.end);
    per[s.type].total++;
    if (!text.includes(value)) { per[s.type].caught++; caught++; }
    else if (missed.length < 6) missed.push(`${s.type}: ${value}`);
  }
  caughtAll += caught;
  if (n > caught && falsePos.length < 6) falsePos.push(text.slice(0, 110));
}

const labels = Object.values(per).reduce((a, p) => a + p.total, 0);
const fp = Math.max(0, tokens - caughtAll);
const recall = labels ? caughtAll / labels : 0;
const precision = tokens ? (tokens - fp) / tokens : 0;
const f1 = precision + recall ? (2 * precision * recall) / (precision + recall) : 0;
const pct = (x) => `${(100 * x).toFixed(1)}%`;

console.log(`${hidden ? "hidden" : "public"} corpus · ${docs.length} texts · ${labels} PII values\n`);
for (const t of TYPES) {
  const p = per[t];
  if (!p.total) continue;
  const r = p.caught / p.total;
  const c = r === 1 ? "\x1b[32m" : r > 0 ? "\x1b[33m" : "\x1b[31m";
  console.log(`${c}${t.padEnd(7)} ${String(p.caught).padStart(4)} / ${String(p.total).padEnd(4)} ${pct(r)}\x1b[0m`);
}
console.log(`\nfalse positives: ${fp}`);
console.log(`precision ${pct(precision)} · recall ${pct(recall)} · \x1b[1mF1 ${pct(f1)}\x1b[0m`);
if (!hidden) {
  if (missed.length) console.log(`\n\x1b[2mmissed, e.g.:\n  ${missed.join("\n  ")}\x1b[0m`);
  if (falsePos.length) console.log(`\x1b[2mfalse positives, e.g.:\n  ${falsePos.join("\n  ")}\x1b[0m`);
}
