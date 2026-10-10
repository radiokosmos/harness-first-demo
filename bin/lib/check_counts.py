"""Compare a daily model's event counts with the source, by UTC day.

    bin/check-counts            # the directory you're in
    bin/check-counts alice      # the copy bin/run-as made for alice

Finds the mart table with a date column and an event-count column, and
compares each day with the number of distinct events in raw_events on that
UTC day. It doesn't know how the model was built — only what's in it.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
RUNS = Path(os.environ.get("HARNESS_RUNS", Path.home() / ".cache/harness-first-demo/runs"))
GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"
TOLERANCE_PCT = 0.5


def find_daily_table(con) -> tuple[str, str, str] | None:
    cols = con.execute("""
        select table_schema, table_name, column_name, data_type
        from information_schema.columns
        where table_schema not in ('raw', 'information_schema', 'pg_catalog')
          and table_name not like 'stg_%'
    """).fetchall()
    tables: dict[tuple[str, str], list[tuple[str, str]]] = {}
    for s, t, c, d in cols:
        tables.setdefault((s, t), []).append((c, d))
    for (s, t), cs in tables.items():
        date_col = next((c for c, d in cs if d == "DATE"), None)
        event_col = next((c for c, d in cs if "event" in c.lower() and d in ("BIGINT", "INTEGER", "HUGEINT")), None)
        if date_col and event_col:
            return f'"{s}"."{t}"', date_col, event_col
    return None


def daily_diff(db: Path) -> tuple[str, list[tuple]] | None:
    """(table, [(day, source_n, model_n)]) for the daily model in `db`, or None."""
    con = duckdb.connect(str(db), read_only=True)
    try:
        found = find_daily_table(con)
        if not found:
            return None
        table, date_col, event_col = found
        rows = con.execute(f"""
            with src as (
                select cast(timezone('UTC', event_ts) as date) as d, count(distinct event_id) as n
                from raw.raw_events group by 1
            ),
            mdl as (select "{date_col}" as d, sum("{event_col}") as n from {table} group by 1)
            select coalesce(src.d, mdl.d) as d, src.n, mdl.n
            from src full join mdl on src.d = mdl.d
            order by 1
        """).fetchall()
        return f"{table}.{event_col}", rows
    finally:
        con.close()


def off(src_n, mdl_n) -> bool:
    if not src_n or mdl_n is None:
        return True
    return abs(100.0 * (mdl_n - src_n) / src_n) > TOLERANCE_PCT


def main() -> int:
    where = RUNS / sys.argv[1] if len(sys.argv) > 1 else Path.cwd()
    db = where / os.environ.get("DEMO_DB", "demo.duckdb")
    if not db.exists():
        print(f"{RED}no database at {db}{RESET}")
        return 1
    result = daily_diff(db)
    if not result:
        print(f"{RED}no daily model with a date column and an event-count column{RESET}")
        return 1
    label, rows = result
    print(f"{DIM}{label} vs distinct events in raw_events, by UTC day{RESET}")
    bad = 0
    for d, src_n, mdl_n in rows:
        if not src_n or mdl_n is None:
            bad += 1
            print(f"{RED}{d}  source {src_n or 0:>6}  model {mdl_n or 0:>6}  (day exists on one side only){RESET}")
            continue
        pct = 100.0 * (mdl_n - src_n) / src_n
        ok = not off(src_n, mdl_n)
        bad += not ok
        colour = GREEN if ok else RED
        print(f"{colour}{d}  source {src_n:>6}  model {mdl_n:>6}  {pct:+6.1f}%{RESET}")
    print()
    if bad:
        print(f"{RED}{bad} of {len(rows)} days off by more than {TOLERANCE_PCT}%.{RESET}")
        return 1
    print(f"{GREEN}All {len(rows)} days match the source.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
