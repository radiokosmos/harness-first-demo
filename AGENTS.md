# AGENTS.md — team layer

dbt project on DuckDB. Run dbt with `DBT_PROFILES_DIR=.`.
Each directory may have its own AGENTS.md — read it before editing files there.
Owners of each area: see `CODEOWNERS`.

## Layers
- Team (this file and directory AGENTS.md) takes precedence over personal notes for code, data, tests and conventions.
- Personal notes win only for how you talk to that person: language, tone, format of replies.
- If two instructions still conflict, stop and say so instead of choosing.

## Conventions
- Models use `fct_` / `dim_` prefixes, snake_case (full list in docs/naming.md).
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
