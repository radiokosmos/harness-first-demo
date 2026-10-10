# Harness First — demo repo

Companion repo for a hands-on tutorial: building an AI agent harness for a data
platform. A small dbt + DuckDB project with synthetic data and deliberate traps.
Every act of the tutorial breaks something and adds one piece of harness.

All data is synthetic (Faker, fixed seeds). No real customers, no real company.

## Setup

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

Fell behind? Every exercise has a checkpoint branch: `git checkout act-N-…`.

## Tools

| Command | What |
|---|---|
| `bin/doctor` | is the machine ready |
| `bin/run-as <who> <task>` | run the agent as Alice or Bob (their personal layer goes into the system prompt) in a throwaway copy |
| `bin/run-many -n N alice bob` | many runs in parallel (agents are not deterministic) |
| `bin/compare alice bob` / `--all` | what each run built; `--all` = the distribution over every run |
| `bin/decisions` | where the agent chose between layers on its own |
| `bin/check-layers` | act 1: is every line of context in the right layer (7 checks) |
| `bin/check-counts [who]` | daily model vs source, by UTC day |
