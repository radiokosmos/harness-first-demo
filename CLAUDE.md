# Project notes

Hi! I'm Alice, I set this repo up. These are the things the agent kept getting wrong, so I wrote them down.

## General

- Always reply in German, I'm in Vienna and it's faster for me to read.
- Don't start answers with "Great question" or similar, just get to the point.
- I like summaries as short bullet lists, max five bullets.
- This is a dbt project on DuckDB. Run everything with `DBT_PROFILES_DIR=.`.
- Python 3.10 is required for the tooling.
- Dev database: dev_wh.duckdb (set DEMO_DB if it complains).
- Commit messages short, imperative, no emojis please.
- I work late — batch your questions in one message instead of asking one by one.
- Q3: we're migrating the marketing models to the new semantic layer, keep that in mind.
- Bob owns the finance models, ask him before touching anything there.

## SQL style

- Lowercase SQL keywords.
- Use CTEs, not nested subqueries.
- One model per file, file name = model name.
- Never `select *` in marts.
- Prefer CTEs over subqueries, they're easier to review.
- Trailing commas are fine, leading commas are not.
- All timestamps are stored in UTC.

## Models

- Models use `fct_` / `dim_` prefixes, snake_case (full list in docs/naming.md).
- Staging models live in `models/staging`, one per source table, prefixed `stg_`.
- Marts live in `models/marts`.
- Macros go in `macros/`, each with a docstring.
- `stg_events` has duplicates from mobile replays; dedupe on `event_id` (keep the earliest `ingested_at`).
- Every model needs `unique` + `not_null` tests on its primary key.
- Sources are declared in `models/staging/_sources.yml`.
- I keep a scratch folder `models/alice_scratch/` for experiments, ignore it.
- For quick prototypes, skip tests, we'll add them later.
- Support tickets contain customer PII in `body`, never copy it into marts.

## Running things

- `dbt build -s <model>` builds and tests one model.
- Never run dbt with `--target prod`.
- I always double-check against prod before handing over: `dbt build --target prod -s <model>`.
- If a seed changes, run `dbt seed --full-refresh`.
- Don't run `dbt clean` without asking, it wipes my target folder.

## Adding a model

When you add a new model, follow these steps:

1. Check the grain of the source: what is one row?
2. Decide the grain of the new model and write it at the top of the SQL as a comment.
3. Check for duplicates in the source on the key you plan to use.
4. Pick the prefix (`fct_` for events/facts, `dim_` for entities).
5. Write the model with CTEs: import CTEs first, then logic, then final select.
6. Add a YAML file next to the model with a description for the model and each column.
7. Add `unique` and `not_null` tests on the primary key.
8. If any column comes from a PII source, add `meta: {pii: true}` to it.
9. Run `dbt build -s <model>` and fix failures.
10. Write a short summary of what you built.

## Misc

- The `raw` schema is loaded from seeds, don't edit the CSVs by hand.
- I prefer seeing numbers rounded to one decimal.
- Ask before adding new packages to `pyproject.toml`.
- If you're not sure about something, ask me, don't guess.
