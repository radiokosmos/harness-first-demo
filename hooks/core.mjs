// The prod guardrail — one core, two runtimes.
// Adapters: hooks/claude-pretooluse.mjs (Claude Code) and .pi/extensions/block-prod.ts (pi).
// Change behaviour here, never in an adapter.

/**
 * Would this shell command run dbt against the prod target?
 *
 * Must block:  dbt build --target prod · dbt run -t prod · dbt build --target=prod
 *              DBT_TARGET=prod dbt build · .venv/bin/dbt build --target prod
 * Must allow:  dbt build --target dev · anything that only *mentions* the flags
 *              (grep, git commit -m "...", echo, editing docs)
 *
 * Tip: a command can chain several commands (&&, ;, |, newlines).
 * Look at each one, and only at commands that actually *are* dbt.
 */
export function isProdRun(command) {
  // TODO: act 2, exercise 2a
  return false;
}

export const REASON =
  "Blocked by the team guardrail: dbt must not run against the prod target from an agent session. " +
  "Use the dev target. Production runs are human-only (AGENTS.md).";
