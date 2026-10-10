"""Act 5: which mistakes keep coming back?

    bin/reflections-report            # digest + candidates
    bin/reflections-report --validate # schema check only

A class seen twice in one repo, or three times anywhere, and not yet promoted,
is a candidate: stop writing it down, write a check.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path.cwd()
FIELDS = ["date", "repo", "severity", "class", "finding", "caught_by", "missed_by", "candidate_check", "promoted"]
SEVERITIES = {"blocker", "major", "minor"}
CLASSES = {"rbac", "cost", "pii", "idempotency", "lineage", "edge-case", "acceptance", "broken-reference", "destroy", "other"}
RED, YELLOW, GREEN, DIM, BOLD, RESET = "\033[31m", "\033[33m", "\033[32m", "\033[2m", "\033[1m", "\033[0m"


def load() -> tuple[list[dict], list[str]]:
    entries, errors = [], []
    for f in sorted((ROOT / "reflections").glob("*.jsonl")):
        for n, line in enumerate(f.read_text().splitlines(), 1):
            if not line.strip():
                continue
            where = f"{f.name}:{n}"
            try:
                e = json.loads(line)
            except json.JSONDecodeError as err:
                errors.append(f"{where} not JSON ({err.msg})")
                continue
            missing = [k for k in FIELDS if k not in e]
            if missing:
                errors.append(f"{where} missing {', '.join(missing)}")
            if e.get("severity") not in SEVERITIES:
                errors.append(f"{where} severity must be one of {sorted(SEVERITIES)}")
            if e.get("class") not in CLASSES:
                errors.append(f"{where} class must be one of {sorted(CLASSES)}")
            entries.append(e)
    return entries, errors


def main() -> int:
    entries, errors = load()
    for e in errors:
        print(f"{RED}✗ {e}{RESET}")
    if "--validate" in sys.argv or errors:
        if not errors:
            print(f"{GREEN}✓ {len(entries)} entries valid{RESET}")
        return 1 if errors else 0

    open_ = [e for e in entries if not e.get("promoted")]
    by_repo_class = Counter((e["repo"], e["class"]) for e in open_)
    by_class = Counter(e["class"] for e in open_)
    print(f"{BOLD}{len(entries)} reflections{RESET} · {len(entries) - len(open_)} promoted to checks\n")
    for cls, n in by_class.most_common():
        print(f"  {n} × {cls}")

    checks = defaultdict(list)
    for e in open_:
        checks[(e["repo"], e["class"])].append(e)
    candidates = [k for k in checks if by_repo_class[k] >= 2 or by_class[k[1]] >= 3]
    print()
    if not candidates:
        print(f"{GREEN}No candidates yet.{RESET}")
        return 0
    for repo, cls in candidates:
        print(f"{YELLOW}candidate: {cls} in {repo} — seen {by_repo_class[(repo, cls)]} times{RESET}")
        for e in checks[(repo, cls)]:
            print(f"    {DIM}{e['date']}  {e['finding']}{RESET}")
        suggestions = sorted({e["candidate_check"] for e in checks[(repo, cls)] if e["candidate_check"] not in ("", "none")})
        for s in suggestions:
            print(f"    → {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
