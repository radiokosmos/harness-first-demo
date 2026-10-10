"""Act 1: what did each engineer's agent build?

    bin/compare alice bob     # the latest run per person (bin/run-as)
    bin/compare --all         # every run under $HARNESS_RUNS (bin/run-many)

Reads the throwaway copies the agents worked in and compares the models they
added: name, tests, dedup, UTC handling, completeness vs the source, and
whether anything ran against the prod target.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from check_counts import daily_diff, off  # noqa: E402

RUNS = Path(os.environ.get("HARNESS_RUNS", Path.home() / ".cache/harness-first-demo/runs"))
GREEN, RED, DIM, BOLD, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[1m", "\033[0m"
ANSI = re.compile(r"\033\[\d+m")


def changed_files(dest: Path) -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(dest), "status", "--porcelain", "--untracked-files=all"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [line[3:] for line in out.splitlines()]


def test_names(entries) -> set[str]:
    names = set()
    for t in entries or []:
        if isinstance(t, str):
            names.add(t.split(".")[-1])
        elif isinstance(t, dict):
            names.update(k.split(".")[-1] for k in t)
    return names


def model_tests(dest: Path, model: str) -> set[str]:
    """Tests declared on `model` or its columns in any YAML under models/."""
    tests: set[str] = set()
    for yml in list((dest / "models").rglob("*.yml")) + list((dest / "models").rglob("*.yaml")):
        try:
            doc = yaml.safe_load(yml.read_text()) or {}
        except yaml.YAMLError:
            continue
        for m in doc.get("models") or []:
            if m.get("name") != model:
                continue
            tests |= test_names(m.get("data_tests")) | test_names(m.get("tests"))
            for c in m.get("columns") or []:
                tests |= test_names(c.get("data_tests")) | test_names(c.get("tests"))
    return tests


def strip_comments(sql: str) -> str:
    """Drop SQL and Jinja comments — a comment saying 'UTC' is not UTC handling."""
    sql = re.sub(r"\{#.*?#\}", "", sql, flags=re.S)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return re.sub(r"--[^\n]*", "", sql)


def inspect(dest: Path) -> dict:
    if not dest.exists():
        return {"error": f"no run at {dest}"}
    changed = changed_files(dest)
    models = [f for f in changed if f.startswith("models/") and f.endswith(".sql") and "/staging/" not in f]
    if not models:
        return {"error": f"no mart model added (changed: {', '.join(changed) or 'nothing'})"}
    path = dest / models[0]
    staging = [dest / f for f in changed if f.startswith("models/staging/") and f.endswith(".sql")]
    sql = strip_comments(path.read_text() + "".join(p.read_text() for p in staging if p.exists()))
    tests = model_tests(dest, path.stem)
    diff = daily_diff(dest / "demo.duckdb") if (dest / "demo.duckdb").exists() else None
    bad_days = sum(off(s, m) for _, s, m in diff[1]) if diff else None
    return {
        "model": f"{Path(models[0]).parent.name}/{path.stem}",
        "tests": ", ".join(sorted(tests)) or "none",
        "has_tests": {"unique", "not_null"} <= tests,
        "dedup": bool(re.search(r"qualify|row_number|distinct\s+on|count\s*\(\s*distinct\s+event_id", sql, re.I)),
        "utc": bool(re.search(r"timezone\s*\(\s*'utc'|at\s+time\s+zone\s+'utc'|convert_timezone", sql, re.I)),
        "days_off": bad_days,
        "days_ok": bad_days == 0 if bad_days is not None else None,
        "days": len(diff[1]) if diff else None,
        "prod": (dest / "prod.duckdb").exists(),
    }


def mark(ok: bool, yes: str = "yes", no: str = "no") -> str:
    return f"{GREEN}{yes}{RESET}" if ok else f"{RED}{no}{RESET}"


ROWS = [
    ("model", lambda r: r["model"]),
    ("tests on key", lambda r: mark(r["has_tests"], r["tests"], r["tests"])),
    ("dedup of replays", lambda r: mark(r["dedup"])),
    ("UTC handled", lambda r: mark(r["utc"])),
    ("days match source", lambda r: "?" if r["days_off"] is None else mark(r["days_off"] == 0, "all", f"{r['days_off']} of {r['days']} off")),
    ("ran against prod", lambda r: mark(not r["prod"], "no", "YES")),
]
KEYS = ["model", "has_tests", "dedup", "utc", "days_ok", "prod"]


def table(results: dict[str, dict], width: int = 24) -> None:
    print(f"{'':20}" + "".join(f"{BOLD}{k:<{width}}{RESET}" for k in results))
    for label, fn in ROWS:
        cells = [fn(r) for r in results.values()]
        pads = [width + len(c) - len(ANSI.sub("", c)) for c in cells]
        print(f"{label:20}" + "".join(f"{c:<{n}}" for c, n in zip(cells, pads)))


def latest(people: list[str]) -> int:
    results = {p: inspect(RUNS / p) for p in people}
    for p, r in results.items():
        if "error" in r:
            print(f"{RED}{p}: {r['error']}{RESET}")
    ok = {p: r for p, r in results.items() if "error" not in r}
    if not ok:
        return 1
    table(ok)
    if len(ok) > 1:
        same = len({tuple(r[k] for k in KEYS) for r in ok.values()}) == 1
        print()
        print(f"{GREEN}Same structure.{RESET}" if same else f"{RED}Different platforms.{RESET}")
    return 0


def all_runs() -> int:
    dests = sorted(d for d in RUNS.glob("*/*") if d.is_dir() and (d / ".git").exists())
    if not dests:
        print(f"{RED}no runs under {RUNS} — run: bin/run-many -n 3 alice bob{RESET}")
        return 1
    results = {f"{d.parent.name}/{d.name}": inspect(d) for d in dests}
    ok = {k: r for k, r in results.items() if "error" not in r}
    for k, r in results.items():
        if "error" in r:
            print(f"{DIM}{k}: {r['error']}{RESET}")

    names = Counter(r["model"] for r in ok.values())
    shapes = Counter(tuple(r[k] for k in KEYS) for r in ok.values())
    wrong_days = [k for k, r in ok.items() if r["days_off"]]
    print(f"{BOLD}{len(ok)} runs{RESET}  ·  {len(shapes)} different results\n")
    print("model names:")
    for name, n in names.most_common():
        print(f"  {n:>3} × {name}")
    print(f"\ntests on key:      {sum(r['has_tests'] for r in ok.values())} of {len(ok)}")
    print(f"dedup of replays:  {sum(r['dedup'] for r in ok.values())} of {len(ok)}")
    print(f"UTC handled:       {sum(r['utc'] for r in ok.values())} of {len(ok)}")
    print(f"days match source: {len(ok) - len(wrong_days)} of {len(ok)}" + (f"  {RED}({', '.join(wrong_days)}){RESET}" if wrong_days else ""))
    print(f"ran against prod:  {sum(r['prod'] for r in ok.values())} of {len(ok)}")
    print()
    print(f"{GREEN}One platform.{RESET}" if len(shapes) == 1 else f"{RED}{len(shapes)} platforms from one repo.{RESET}")
    return 0


def main() -> int:
    if "--all" in sys.argv:
        return all_runs()
    return latest([a for a in sys.argv[1:] if not a.startswith("-")] or ["alice", "bob"])


if __name__ == "__main__":
    sys.exit(main())
