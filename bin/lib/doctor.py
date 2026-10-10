"""Is your machine ready for the tutorial?

    bin/doctor

This is also the first piece of harness: before an agent starts, check that
its world is what it thinks it is.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GREEN, RED, YELLOW, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[0m"


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=ROOT)
        return p.returncode == 0, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def main() -> int:
    results: list[tuple[str, bool | None, str]] = []

    ok, out = run([str(ROOT / ".venv/bin/dbt"), "--version"])
    results.append(("dbt in .venv", ok, "" if ok else "run: uv sync"))

    try:
        import duckdb  # noqa: F401
        results.append(("duckdb", True, ""))
    except ImportError:
        results.append(("duckdb", False, "run: uv sync"))

    seeds = all((ROOT / "seeds" / f).exists() for f in ("raw_events.csv", "support_tickets.csv"))
    results.append(("synthetic data", seeds, "" if seeds else "run: uv run python data/generate.py"))

    node = shutil.which("node")
    results.append(("node (for agent hooks)", bool(node), "" if node else "install Node 20+"))

    runtimes = [r for r in ("pi", "claude", "codex") if shutil.which(r)]
    results.append(("agent runtime", bool(runtimes), ", ".join(runtimes) if runtimes else "install pi, Claude Code or Codex"))

    rsync = shutil.which("rsync")
    results.append(("rsync (bin/run-as)", bool(rsync), ""))

    width = max(len(n) for n, _, _ in results)
    for name, ok, note in results:
        mark = f"{GREEN}✓{RESET}" if ok else f"{RED}✗{RESET}"
        print(f"{mark} {name:<{width}}  {note}")
    failed = sum(1 for _, ok, _ in results if not ok)
    print()
    if failed:
        print(f"{RED}{failed} problem(s). Fix them, or pair up with your neighbour.{RESET}")
        return 1
    print(f"{GREEN}Ready.{RESET} Model access is checked on the first agent run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
