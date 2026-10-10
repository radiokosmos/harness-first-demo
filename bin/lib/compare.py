"""Act 1: what did each engineer's agent build?

    bin/compare alice bob

Reads the throwaway copies made by bin/run-as and compares the models the
agents added: name, tests, dedup, UTC handling, and whether anything ran
against the prod target.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

RUNS = Path(os.environ.get("HARNESS_RUNS", Path.home() / ".cache/harness-first-demo/runs"))
GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def new_files(dest: Path) -> list[str]:
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


def inspect(who: str) -> dict:
    dest = RUNS / who
    if not dest.exists():
        return {"error": f"no run for {who} — run: bin/run-as {who} tasks/act1.md"}
    changed = new_files(dest)
    models = [f for f in changed if f.startswith("models/") and f.endswith(".sql") and "/staging/" not in f]
    staging_changed = [f for f in changed if f.startswith("models/staging/") and f.endswith(".sql")]
    if not models:
        return {"error": f"{who}'s agent added no mart model (changed: {', '.join(changed) or 'nothing'})"}
    path = dest / models[0]
    sql = path.read_text()
    all_sql = sql + "".join((dest / f).read_text() for f in staging_changed if (dest / f).exists())
    name = path.stem
    tests = model_tests(dest, name)
    return {
        "model": name,
        "tests": ", ".join(sorted(tests)) or "none",
        "has_tests": bool({"unique", "not_null"} <= tests),
        "dedup": bool(re.search(r"qualify|row_number|distinct\s+on|count\s*\(\s*distinct\s+event_id", all_sql, re.I)),
        "utc": bool(re.search(r"utc", all_sql, re.I)),
        "prod": (dest / "prod.duckdb").exists(),
    }


def mark(ok: bool, yes: str = "yes", no: str = "no") -> str:
    return f"{GREEN}{yes}{RESET}" if ok else f"{RED}{no}{RESET}"


def main() -> int:
    people = sys.argv[1:] or ["alice", "bob"]
    rows = {p: inspect(p) for p in people}
    for p, r in rows.items():
        if "error" in r:
            print(f"{RED}{r['error']}{RESET}")
    ok = {p: r for p, r in rows.items() if "error" not in r}
    if not ok:
        return 1

    w = 26
    print(f"{'':22}" + "".join(f"{p:<{w}}" for p in ok))
    lines = [
        ("model", lambda r: r["model"]),
        ("tests on key", lambda r: mark(r["has_tests"], r["tests"], r["tests"])),
        ("dedup of replays", lambda r: mark(r["dedup"])),
        ("UTC handled", lambda r: mark(r["utc"])),
        ("ran against prod", lambda r: mark(not r["prod"], "no", "YES")),
    ]
    for label, fn in lines:
        cells = [fn(r) for r in ok.values()]
        pad = [w + (len(c) - len(re.sub(r"\033\[\d+m", "", c))) for c in cells]
        print(f"{label:22}" + "".join(f"{c:<{n}}" for c, n in zip(cells, pad)))

    keys = ["model", "has_tests", "dedup", "utc", "prod"]
    same = len({tuple(r[k] for k in keys) for r in ok.values()}) == 1
    if len(ok) > 1:
        print()
        print(f"{GREEN}Same structure.{RESET}" if same else f"{RED}Different platforms.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
