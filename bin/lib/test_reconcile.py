"""bin/test-reconcile — table-driven cases for reconcile itself.

Each case names a version of fct_activity_daily and what reconcile must say
about it. The versions are built here from raw.raw_events, in a scratch
database with dbt's session settings (profiles.yml), so the cases don't
depend on what the model in models/ looks like today.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

import duckdb

sys.path.insert(0, str(Path(__file__).parent))
from reconcile import render, run_checks, session_settings  # noqa: E402

ROOT = Path.cwd()
GREEN, RED, RESET = "\033[32m", "\033[31m", "\033[0m"

# Versions of fct_activity_daily: how each one turns event_ts into a day.
VERSIONS = {
    "as_committed": "cast(event_ts as date)",  # models/marts/fct_activity_daily.sql as committed in act 1
    "utc_day": "cast(timezone('UTC', event_ts) as date)",  # the same, with the day taken in UTC
}

cases = [
    ("as_committed", "runs"),  # three checks, a row per day
    ("as_committed", "completeness has source numbers"),
    ("as_committed", "keys has source numbers"),
    # found after the agent's reconcile passed everything above: it took "a day" the way the model does
    ("as_committed", "FAIL"),  # we know this version is wrong: bin/check-counts, 14 of 15 days off
    ("utc_day", "PASS"),  # and the right one passes: the TODO stub said FAIL to everything
]


def build(db: Path, scratch: Path) -> None:
    con = duckdb.connect(str(scratch))
    try:
        for key, value in session_settings().items():
            con.execute(f"SET {key} = '{value}'")
        con.execute(f"attach '{db}' as src (read_only)")
        con.execute("create schema raw")
        con.execute("create table raw.raw_events as select * from src.raw.raw_events")
        for name, day in VERSIONS.items():
            con.execute(f"""
                create table main.{name} as
                select {day} as activity_date,
                       count(distinct user_id) as active_users,
                       count(distinct event_id) as event_count
                from raw.raw_events group by 1
            """)
    finally:
        con.close()


def judge(results: list[tuple[str, list[tuple]]], expect: str) -> tuple[bool, str]:
    by = dict(results)
    if expect == "runs":
        ok = [name for name, rows in results if rows] == ["completeness", "keys", "nulls"]
        return ok, "ran" if ok else "a check returned no rows"
    if expect.endswith("has source numbers"):
        ok = any(src is not None for _, src, _ in by[expect.split()[0]])
        return ok, "source numbers" if ok else "no source numbers"
    verdict = "PASS" if render("", results)[1] else "FAIL"
    return verdict == expect, verdict


def main() -> int:
    db = ROOT / os.environ.get("DEMO_DB", "demo.duckdb")
    tmp = Path(tempfile.mkdtemp(prefix="test-reconcile-"))
    try:
        try:
            build(db, tmp / "versions.duckdb")
        except duckdb.Error as e:
            print(f"{RED}can't build the versions from {db.name}: {e}\nload the source first: DBT_PROFILES_DIR=. .venv/bin/dbt seed{RESET}")
            return 2
        failed = 0
        for version, expect in cases:
            try:
                ok, got = judge(run_checks(version, tmp / "versions.duckdb"), expect)
            except Exception as e:  # noqa: BLE001 — a crash in reconcile is a failed case
                ok, got = False, f"error: {str(e).splitlines()[0]}"
            failed += not ok
            mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
            print(f"{mark} {version:12} → {expect}{'' if ok else f'   {RED}(got {got}){RESET}'}")
        print(f"\n{RED if failed else GREEN}{len(cases) - failed} of {len(cases)}{RESET}")
        return 1 if failed else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
