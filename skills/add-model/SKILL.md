---
name: add-model
description: Add a new dbt model (staging or mart) — grain, dedup, tests, PII tags. Use whenever you create a new model.
---

# Add a model

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
