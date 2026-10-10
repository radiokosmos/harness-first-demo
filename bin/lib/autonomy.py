"""Act 2: how far may the agent go on this change?

    bin/autonomy <path> [<path> ...]

Resolves the zone from autonomy.yaml, then applies escalators: a model that
reads PII (a source or column tagged meta.pii) is at least checkpoint-each-stage,
whatever its folder says.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

import yaml

ROOT = Path.cwd()
GREEN, YELLOW, RED, DIM, RESET = "\033[32m", "\033[33m", "\033[31m", "\033[2m", "\033[0m"
COLOURS = [GREEN, YELLOW, RED, RED]


def pii_sources() -> set[tuple[str, str]]:
    found = set()
    for yml in (ROOT / "models").rglob("*.yml"):
        doc = yaml.safe_load(yml.read_text()) or {}
        for src in doc.get("sources") or []:
            for t in src.get("tables") or []:
                if (t.get("meta") or {}).get("pii") or any((c.get("meta") or {}).get("pii") for c in t.get("columns") or []):
                    found.add((src["name"], t["name"]))
    return found


def escalators(path: str) -> list[str]:
    p = ROOT / path
    if not (p.suffix == ".sql" and p.exists()):
        return []
    sql = p.read_text()
    hits = []
    for src, table in pii_sources():
        if re.search(rf"source\(\s*['\"]{src}['\"]\s*,\s*['\"]{table}['\"]\s*\)", sql):
            hits.append(f"pii (reads {src}.{table})")
    if re.search(r"\b(drop|truncate|delete\s+from)\b", sql, re.I):
        hits.append("destroy")
    return hits


def resolve(path: str, cfg: dict) -> tuple[str, list[str]]:
    levels = cfg["levels"]
    level = cfg["default"]
    for zone in cfg["zones"]:
        if any(fnmatch.fnmatch(path, pat) or fnmatch.fnmatch(path, pat.replace("/**", "/*/*")) for pat in zone["paths"]):
            level = zone["level"]
            break
    esc = escalators(path)
    if esc and levels.index(level) < levels.index("checkpoint-each-stage"):
        level = "checkpoint-each-stage"
    return level, esc


def main() -> int:
    cfg = yaml.safe_load((ROOT / "autonomy.yaml").read_text())
    if len(sys.argv) < 2:
        print("usage: bin/autonomy <path> [<path> ...]")
        return 2
    for path in sys.argv[1:]:
        level, esc = resolve(path, cfg)
        colour = COLOURS[cfg["levels"].index(level)]
        note = f"  {DIM}escalator: {', '.join(esc)}{RESET}" if esc else ""
        print(f"{colour}{level:24}{RESET} {path}{note}")
    print(f"\n{DIM}human-only, always: {'; '.join(cfg['human_only'])}{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
