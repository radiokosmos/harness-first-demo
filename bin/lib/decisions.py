"""Act 1: where did the agent decide between layers on its own?

    bin/decisions             # every run log under $HARNESS_RUNS

Scans agent logs for sentences where the agent noticed two sources of
instructions disagreeing and picked one — the decisions nobody owns.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

RUNS = Path(os.environ.get("HARNESS_RUNS", Path.home() / ".cache/harness-first-demo/runs"))
BOLD, DIM, RESET = "\033[1m", "\033[2m", "\033[0m"

SOURCE = re.compile(r"CLAUDE\.md|AGENTS\.md|your notes|personal notes|your preference|repo's|the repo|Alice's|Bob's|team", re.I)
CHOICE = re.compile(r"\b(but|however|followed|chose|went with|instead|conflict|contradict|override|ignored|took precedence|prioriti[sz]ed)\b", re.I)
SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def decisions(text: str) -> list[str]:
    found = []
    sentences = [s for line in text.splitlines() for s in SENTENCE_END.split(line)]
    for s in sentences:
        s = s.strip(" -*•\t")
        if SOURCE.search(s) and CHOICE.search(s) and 25 < len(s) < 300:
            found.append(s)
    return list(dict.fromkeys(found))


def main() -> int:
    logs = sorted(RUNS.glob("**/*.log"))
    total = 0
    for log in logs:
        found = decisions(log.read_text(errors="replace"))
        if not found:
            continue
        print(f"{BOLD}{log.relative_to(RUNS)}{RESET}")
        for s in found:
            print(f"  “{s}”")
        total += len(found)
    print(f"\n{DIM}{total} decisions between layers that nobody asked the agent to make{RESET}" if total else "no decisions found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
