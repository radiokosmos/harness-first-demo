"""Act 5: does the harness still agree with itself?

    bin/drift-check

  refs       a path mentioned in agent context that doesn't exist
  budget     always-loaded context over its line budget
  stale      a model name in agent context that isn't a model any more
  dead-hook  a guardrail that never fired in any recorded run (dead — or perfect?)

The first three fail the check; dead-hook is a question for a human.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

ROOT = Path.cwd()
RUNS = Path(os.environ.get("HARNESS_RUNS", Path.home() / ".cache/harness-first-demo/runs"))
RED, YELLOW, GREEN, DIM, RESET = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[0m"
BUDGET = {"AGENTS.md": 40}


def context_files() -> list[Path]:
    files = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]
    files += sorted((ROOT / "models").rglob("AGENTS.md")) + sorted((ROOT / "macros").rglob("AGENTS.md"))
    files += sorted((ROOT / "skills").rglob("SKILL.md")) + sorted((ROOT / "people").glob("*.md"))
    return [f for f in files if f.exists()]


def lines(p: Path) -> list[tuple[int, str]]:
    out, fenced = [], False
    for i, line in enumerate(p.read_text().splitlines(), 1):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced:
            out.append((i, line))
    return out


GENERATED = {"EVIDENCE.md"}  # produced while the agent works, not checked in

PATH = re.compile(r"(?<![\w<@])((?:[\w.-]+/)*[\w.-]+\.(?:md|ya?ml|sql|mjs|js|ts|py|csv|jsonl))\b")


def check_refs() -> list[str]:
    issues = []
    for f in context_files():
        for n, line in lines(f):
            for m in PATH.finditer(line):
                ref = m.group(1)
                if any(c in ref for c in "<>*") or ref.startswith(".") or ref in GENERATED:
                    continue
                if not ((ROOT / ref).exists() or (f.parent / ref).exists()):
                    issues.append(f"{f.relative_to(ROOT)}:{n}  {ref} does not exist")
    return issues


def check_budget() -> list[str]:
    issues = []
    for name, limit in BUDGET.items():
        p = ROOT / name
        if p.exists():
            n = sum(1 for _, l in lines(p) if l.strip())
            if n > limit:
                issues.append(f"{name}  {n} lines (budget {limit}) — lessons belong in checks, not in the map")
    return issues


MODEL = re.compile(r"\b((?:stg|fct|dim)_[a-z0-9_]+)\b")


def check_stale() -> list[str]:
    models = {p.stem for p in (ROOT / "models").rglob("*.sql")}
    issues = []
    for f in context_files():
        for n, line in lines(f):
            for m in MODEL.finditer(line):
                name = m.group(1)
                if name.endswith("_") or name in models:
                    continue
                issues.append(f"{f.relative_to(ROOT)}:{n}  {name} is not a model (models: {', '.join(sorted(models))})")
    return issues


HOOKS = {
    # source: (where it is defined, how its firing shows up in logs)
    "block-prod": ("hooks/core.mjs", re.compile(r"Blocked by the team guardrail|\"source\":\s*\"block-prod\"")),
    "pii-filter": (".pi/extensions/pii-filter.ts", re.compile(r"\[pii-filter\]|\"source\":\s*\"pii-filter\"")),
    "sql-guard": ("guards/day-boundary.mjs", re.compile(r"\[sql-guard\]|\"source\":\s*\"sql-guard\"")),
}


def check_dead_hooks() -> list[str]:
    logs = [p for base in (ROOT / "recordings", RUNS) if base.exists()
            for p in base.rglob("*") if p.is_file() and p.suffix in (".log", ".txt", ".jsonl", ".out")]
    issues = []
    for name, (where, rx) in HOOKS.items():
        if not (ROOT / where).exists():
            continue
        fired = sum(len(rx.findall(p.read_text(errors="replace"))) for p in logs)
        if fired == 0:
            issues.append(f"{name} ({where}) fired 0 times in {len(logs)} recorded logs — dead, or perfect?")
    return issues


CHECKS = [
    ("refs", check_refs, True),
    ("budget", check_budget, True),
    ("stale", check_stale, True),
    ("dead-hook", check_dead_hooks, False),
]


def main() -> int:
    failed = 0
    for name, fn, blocking in CHECKS:
        issues = fn()
        if not issues:
            print(f"{GREEN}✓ {name}{RESET}")
            continue
        colour = RED if blocking else YELLOW
        failed += blocking
        print(f"{colour}{'✗' if blocking else '?'} {name}{RESET}")
        for i in issues:
            print(f"    {DIM}{i}{RESET}")
    print()
    print(f"{RED}{failed} drift check(s) failing{RESET}" if failed else f"{GREEN}No drift.{RESET}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
