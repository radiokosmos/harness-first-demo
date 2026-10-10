"""Act 2: is the task actually done? Decided by artifacts, not by the agent.

    bin/check-done <model>

1. EVIDENCE.md exists and is exactly what bin/reconcile produces right now
   (hand-written or edited evidence fails).
2. Every evidence check passes.
3. Planned = executed: every test declared on the model in YAML ran in the
   last dbt invocation (target/run_results.json) and passed — none skipped,
   none missing.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent))
from reconcile import render, run_checks  # noqa: E402

ROOT = Path.cwd()
GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def planned_tests(model: str) -> set[str]:
    """Generic test names declared on the model and its columns, as dbt names them."""
    planned: set[str] = set()
    for yml in list((ROOT / "models").rglob("*.yml")) + list((ROOT / "models").rglob("*.yaml")):
        doc = yaml.safe_load(yml.read_text()) or {}
        for m in doc.get("models") or []:
            if m.get("name") != model:
                continue
            for c in m.get("columns") or []:
                for t in (c.get("data_tests") or []) + (c.get("tests") or []):
                    name = t if isinstance(t, str) else next(iter(t))
                    planned.add(f"{name.split('.')[-1]}_{model}_{c['name']}")
    return planned


def executed_tests(model: str) -> dict[str, str]:
    path = ROOT / "target" / "run_results.json"
    if not path.exists():
        return {}
    out = {}
    for r in json.loads(path.read_text()).get("results", []):
        uid = r.get("unique_id", "")
        if uid.startswith("test.") and model in uid:
            out[uid.split(".")[2]] = r.get("status", "?")
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: bin/check-done <model>")
        return 2
    model = sys.argv[1]
    problems: list[str] = []

    evidence = ROOT / "EVIDENCE.md"
    fresh, ok = render(model, run_checks(model, ROOT / os.environ.get("DEMO_DB", "demo.duckdb")))
    if not evidence.exists():
        problems.append("no EVIDENCE.md — run bin/reconcile " + model)
    elif evidence.read_text() != fresh:
        problems.append("EVIDENCE.md differs from what bin/reconcile produces now — evidence is generated, not written")
    if not ok:
        problems.append("evidence checks fail — see EVIDENCE.md")

    planned = planned_tests(model)
    executed = executed_tests(model)
    if not planned:
        problems.append(f"no tests declared on {model} in YAML")
    for t in sorted(planned):
        status = next((s for name, s in executed.items() if name.startswith(t)), None)
        if status is None:
            problems.append(f"planned test did not run: {t}")
        elif status != "pass":
            problems.append(f"test {t}: {status}")

    if problems:
        for p in problems:
            print(f"{RED}✗ {p}{RESET}")
        print(f"\n{RED}NOT DONE{RESET}")
        return 1
    print(f"{GREEN}✓ evidence generated and passing · {len(planned)} planned tests ran and passed{RESET}")
    print(f"\n{GREEN}DONE{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
