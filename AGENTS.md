# AGENTS.md — team layer

dbt project on DuckDB. Run dbt with `DBT_PROFILES_DIR=.`.
Each directory may have its own AGENTS.md — read it before editing files there.
Owners of each area: see `CODEOWNERS`.

## Layers
- Team (this file and directory AGENTS.md) takes precedence over personal notes for code, data, tests and conventions.
- Personal notes win only for how you talk to that person: language, tone, format of replies.
- If two instructions still conflict, stop and say so instead of choosing.

## Conventions
- Models use `fct_` / `dim_` prefixes, snake_case.
- Daily aggregates are named `fct_<subject>_daily`, one row per day, in `models/marts/`.
- One model per file, file name = model name.
- Lowercase SQL keywords; CTEs, not nested subqueries; trailing commas.
- Never `select *` in marts.
- Every model needs `unique` + `not_null` tests on its primary key.
- All timestamps are stored in UTC.
- Support tickets contain customer PII in `body`; never copy it into marts.

## Running things
- `dbt build -s <model>` builds and tests one model.
- Never run dbt with `--target prod`.
- If a seed changes, run `dbt seed --full-refresh`.
- Don't run `dbt clean`; ask before adding packages to `pyproject.toml`.
- The `raw` schema is loaded from seeds; don't edit the CSVs by hand.

## Guardrails
- `hooks/` blocks dbt runs against prod for every agent runtime (Claude Code, pi).
- How far an agent may go on its own: `autonomy.yaml` (`bin/autonomy <path>`).

## Skills
- Adding a model: `skills/add-model/SKILL.md`.

## Lessons learned
<!-- Promoted to checks and removed from here: day boundaries (bin/lint-models), per-day counts and tests-ran (bin/check-done), prod (hooks/core.mjs). -->
- If dev looks broken, report it instead of switching targets.
- Support ticket bodies contain PII — don't paste them into replies.
- Tokens like <EMAIL_3> are pseudonyms; you can use them in SQL as they are.
- If the database file looks wrong, stop and report — don't delete or re-seed it.
- Don't rebuild seeds to "fix" the environment.
- When a nightly run can't reach the warehouse, say so in the report.
- Prefer CTEs, keep models small.
