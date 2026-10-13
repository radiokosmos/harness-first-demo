// The prod guardrail — one core, two runtimes.
// Adapters: hooks/claude-pretooluse.mjs (Claude Code) and .pi/extensions/block-prod.ts (pi).
// Change behaviour here, never in an adapter.

/** Would this shell command run dbt against the prod target? */
export function isProdRun(command) {
  // TODO: act 2, exercise 2a
  return false;
}

export const REASON =
  "Blocked by the team guardrail: dbt must not run against the prod target from an agent session. " +
  "Use the dev target. Production runs are human-only (AGENTS.md).";
