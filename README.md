# Harness First — demo repo

Companion repo for a hands-on tutorial: building an AI agent harness for a data
platform. A small dbt + DuckDB project with synthetic data and deliberate traps.
Every act of the tutorial breaks something and adds one piece of harness.

All data is synthetic (Faker, fixed seeds). No real customers, no real company.

## Setup

**Online, no installs:** [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/radiokosmos/harness-first-demo) — the devcontainer installs everything, generates the data and runs `bin/doctor`. Then log in to one agent runtime (`pi` → `/login`, or `claude` → `/login`), or set `ANTHROPIC_API_KEY`.

**Locally:**

```bash
uv sync
uv run python data/generate.py     # seeds/ and corpus/
DBT_PROFILES_DIR=. .venv/bin/dbt seed
bin/doctor
```

You need one agent runtime: [pi](https://pi.dev), Claude Code or Codex, logged in.

## Acts

| Act | Branch | You build |
|---|---|---|
| 1. A second engineer joins | `act-1-start` | context layers with owners |
| 2. Plausible, wrong SQL | `act-2-start` | a must-rule as code, data evidence |
| 3. The agent sees customer data | `act-3-start` | PII masking before the LLM call |
| 4. You leave the loop | `act-4-start` | a heartbeat from run artifacts |
| 5. The harness rots | `act-5-start` | mistake → check |

Recorded runs for the stage live in `recordings/`.

Not coding along? That's fine — every exercise is also done live by the presenter, and every checkpoint branch is a complete solution.

Fell behind? Every exercise has a checkpoint branch: `git checkout act-N-…`.

## Tools

| Command | Act | What |
|---|---|---|
| `bin/doctor` | — | is the machine ready |
| `bin/stage <act>` | presenter | the presenter's terminal script: one step per Enter, agent output from recordings |
| `bin/run-as <who> <task>` | 1+ | run the agent as Alice or Bob (their personal layer goes into the system prompt) in a throwaway copy |
| `bin/run-many -n N alice bob` | 1+ | many runs in parallel (agents are not deterministic) |
| `bin/compare alice bob` / `--all` | 1 | what each run built; `--all` = the distribution over every run |
| `bin/decisions` | 1 | where the agent chose between layers on its own |
| `bin/check-layers` | 1 | is every line of context in the right layer (7 checks) |
| `bin/check-counts [who]` | 1–2 | daily model vs source, by UTC day |
| `bin/test-hook` | 2 | cases for the prod guardrail (`hooks/core.mjs`) |
| `bin/reconcile <model>` · `bin/check-done <model>` | 2 | evidence on data; done = generated evidence + planned tests ran |
| `bin/autonomy <path>` | 2 | how far an agent may go on a change (`autonomy.yaml`) |
| `bin/pii-score [--hidden]` | 3 | the PII masker (`pii/masker.mjs`) on a labelled corpus |
| `bin/show-provider-payload [who]` | 3 | what actually left the machine |
| `bin/run-headless <task> --scenario …` · `bin/verify-run <dir>` | 4 | an unattended run, and checking it by artifacts |
| `bin/drift-check` · `bin/reflections-report` | 5 | does the harness agree with itself; which mistakes keep coming back |
| `bin/test-guard` · `bin/lint-models` | 5 | the day-boundary guard |

Tools for later acts exist on their branches. `recordings/` has real runs of every act.
