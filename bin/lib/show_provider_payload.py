"""Act 3: what did the last request to the model provider contain?

    bin/show-provider-payload [who]

Reads the payload log the pi PII extension writes (PII_PAYLOAD_LOG; bin/run-as
puts it next to the run) and shows the PII-looking values that left the machine.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

RUNS = Path(os.environ.get("HARNESS_RUNS", Path.home() / ".cache/harness-first-demo/runs"))
RED, GREEN, DIM, BOLD, RESET = "\033[31m", "\033[32m", "\033[2m", "\033[1m", "\033[0m"

PATTERNS = {
    "EMAIL": re.compile(r"[A-Za-z0-9._%+-]+@(?!corp\.example)[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "PHONE": re.compile(r"\+\d[\d\s\-]{8,}\d"),
    "IBAN": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "CARD": re.compile(r"\b(?:\d[ -]?){15}\d\b"),
}


def strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, list):
        for x in v:
            yield from strings(x)
    elif isinstance(v, dict):
        for x in v.values():
            yield from strings(x)


def main() -> int:
    who = sys.argv[1] if len(sys.argv) > 1 else "alice"
    log = Path(os.environ.get("PII_PAYLOAD_LOG", RUNS / f"{who}.payload.jsonl"))
    if not log.exists():
        print(f"{RED}no payload log at {log} — run the agent with pi via bin/run-as{RESET}")
        return 1
    requests = [json.loads(l) for l in log.read_text().splitlines() if l.strip()]
    found: Counter = Counter()
    seen: dict[str, str] = {}
    for req in requests:
        for s in strings(req):
            for kind, rx in PATTERNS.items():
                for m in rx.finditer(s):
                    found[kind] += 1
                    if m.group() not in seen and len(seen) < 8:
                        a, b = max(0, m.start() - 40), min(len(s), m.end() + 30)
                        seen[m.group()] = s[a:m.start()] + f"{RED}{BOLD}{m.group()}{RESET}" + s[m.end():b]
    print(f"{DIM}{len(requests)} requests to the model provider · {log}{RESET}\n")
    if not found:
        print(f"{GREEN}No PII-looking values left the machine.{RESET}")
        return 0
    for snippet in seen.values():
        print("  …" + snippet.replace("\n", " ") + "…")
    print(f"\n{RED}Left the machine: {', '.join(f'{k}×{v}' for k, v in found.most_common())}{RESET}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
