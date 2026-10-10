// bin/lint-models — run the day-boundary guard over every model.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { findBareDayCasts, ADVICE } from "./day-boundary.mjs";

const walk = (d) => readdirSync(d).flatMap((f) => {
  const p = join(d, f);
  return statSync(p).isDirectory() ? walk(p) : p.endsWith(".sql") ? [p] : [];
});

let n = 0;
for (const f of walk("models")) {
  for (const hit of findBareDayCasts(readFileSync(f, "utf8"))) {
    n++;
    console.log(`\x1b[31m${f}:${hit.line}\x1b[0m  ${hit.text.trim()}`);
  }
}
if (n) console.log(`\n\x1b[31m${n} day boundary issue(s)\x1b[0m — ${ADVICE}`);
else console.log("\x1b[32m✓ no session-local day boundaries\x1b[0m");
process.exit(n ? 1 : 0);
