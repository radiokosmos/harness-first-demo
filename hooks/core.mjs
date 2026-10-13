// The prod guardrail — one core, two runtimes.
// Adapters: hooks/claude-pretooluse.mjs (Claude Code) and .pi/extensions/block-prod.ts (pi).
// Change behaviour here, never in an adapter.

/**
 * Would this shell command run dbt against the prod target?
 *
 * Only commands that actually *run* dbt count. The line is split into commands
 * (&&, ||, ;, |, newlines, quotes respected); for each one we find the program
 * it runs, past VAR=value prefixes and launchers like `uv run`. Its target is
 * --target / -t, else DBT_TARGET: set in front of the command, or exported
 * earlier in the same line.
 *
 * Cases people found and pinned in hooks/test-hook.mjs:
 *   a docs edit that mentions the command must pass (a guard that blocks docs gets turned off);
 *   `export DBT_TARGET=prod; dbt build` and `uv run dbt …` must not.
 */
export function isProdRun(command) {
  const lineEnv = {}; // `export DBT_TARGET=prod; dbt build`: set once, seen by every later command
  return splitCommands(command).some((words) => {
    if (words[0] === "export" || words.every(isAssignment)) {
      for (const w of words) if (isAssignment(w)) assign(lineEnv, w);
      return false;
    }
    const env = { ...lineEnv };
    const [program, ...args] = unwrap(words, env);
    return isDbt(program) && target(args, env) === "prod";
  });
}

const isAssignment = (word) => /^[A-Za-z_][A-Za-z0-9_]*=/.test(word ?? "");
const assign = (env, word) => { const i = word.indexOf("="); env[word.slice(0, i)] = word.slice(i + 1); };
const isDbt = (program) => /(^|\/)dbt$/.test(program ?? "") || program === "dbt.cli.main";

// Skip what runs in front of the program: VAR=value, `uv run`, `poetry run`, `python -m`, `env`.
const RUNNERS = ["uv", "poetry", "pipenv", "pdm", "hatch"];
const PREFIXES = ["env", "exec", "command", "nohup", "time"];
function unwrap(words, env) {
  for (;;) {
    while (isAssignment(words[0])) assign(env, words.shift());
    if (RUNNERS.includes(words[0]) && words[1] === "run") words = words.slice(2);
    else if (/(^|\/)python3?$/.test(words[0] ?? "") && words[1] === "-m") words = words.slice(2);
    else if (PREFIXES.includes(words[0])) words = words.slice(1);
    else return words;
  }
}

// dbt's target: --target / -t on the command line wins over DBT_TARGET.
function target(args, env) {
  for (let i = 0; i < args.length; i++) {
    if (args[i] === "--target" || args[i] === "-t") return args[i + 1];
    if (args[i].startsWith("--target=")) return args[i].slice("--target=".length);
  }
  return env.DBT_TARGET;
}

// Split a shell line into commands (on &&, ||, ;, |, newlines) and each command
// into words, respecting quotes. Good enough for a guardrail; not a shell parser.
function splitCommands(line) {
  const commands = [[]];
  let word = "", quote = null, started = false;
  const pushWord = () => { if (started) commands.at(-1).push(word); word = ""; started = false; };
  for (let i = 0; i < line.length; i++) {
    const c = line[i];
    if (quote) {
      if (c === quote) quote = null; else word += c;
      continue;
    }
    if (c === "'" || c === '"') { quote = c; started = true; continue; }
    if (/\s/.test(c) && c !== "\n") { pushWord(); continue; }
    if (c === "\n" || c === ";" || c === "|" || c === "&") {
      pushWord();
      if (commands.at(-1).length) commands.push([]);
      continue;
    }
    word += c; started = true;
  }
  pushWord();
  return commands.filter((c) => c.length);
}

export const REASON =
  "Blocked by the team guardrail: dbt must not run against the prod target from an agent session. " +
  "Use the dev target. Production runs are human-only (AGENTS.md).";
