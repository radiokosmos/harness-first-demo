# Recordings

Real agent runs kept for the stage — live agents are slow and non-deterministic.
Each folder has the files the agents added, their logs, and `summary.txt`
(`bin/compare --all` + `bin/decisions`).

| Folder | Repo state | Runs |
|---|---|---|
| `act1/before` | `act-1-start` (monolithic CLAUDE.md) | pi × 8, Claude Code × 6 |
| `act1/after` | `act-1-layers` (layers + precedence) | pi × 6, Claude Code × 4 |

Models: pi with `claude-sonnet-5`, Claude Code with `claude-sonnet-5-5`.
To compare a recording yourself: `HARNESS_RUNS=<scratch copy of runs> bin/compare --all`.
