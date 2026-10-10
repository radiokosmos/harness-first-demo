"""Act 1: is every line of agent context in the right layer?

    bin/check-layers

Six checks. Run it as often as you like — it only reads files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEAM_BUDGET = 40

GREEN, RED, DIM, RESET = "\033[32m", "\033[31m", "\033[2m", "\033[0m"


def read(p: Path) -> str:
    return p.read_text() if p.exists() else ""


def content_lines(text: str) -> list[str]:
    """Non-blank lines outside fenced code blocks."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if not fenced and line.strip():
            out.append(line)
    return out


def context_files() -> dict[str, str]:
    """Everything an agent may load as context, keyed by repo-relative path."""
    files = [ROOT / "CLAUDE.md", ROOT / "AGENTS.md"]
    files += sorted((ROOT / "models").rglob("AGENTS.md"))
    files += sorted((ROOT / "skills").rglob("SKILL.md"))
    files += sorted((ROOT / "people").glob("*.md"))
    return {str(p.relative_to(ROOT)): read(p) for p in files if p.exists()}


PERSONAL_MARKERS = [
    (re.compile(r"\b(I|I'm|I've|I'd)\b"), "first person"),
    (re.compile(r"\b(my|me)\b", re.I), "first person"),
    (re.compile(r"\bGerman\b"), "reply language"),
    (re.compile(r"emoji", re.I), "commit style"),
    (re.compile(r"great question", re.I), "answer style"),
    (re.compile(r"bullet", re.I), "summary style"),
    (re.compile(r"work late", re.I), "working hours"),
    (re.compile(r"rounded to", re.I), "number formatting"),
]


def check_team_impersonal(ctx: dict[str, str]) -> list[str]:
    team = {k: v for k, v in ctx.items() if k.endswith("AGENTS.md")}
    if "AGENTS.md" not in team:
        return ["AGENTS.md does not exist yet — the team layer lives there"]
    issues = []
    for path, text in team.items():
        for line in content_lines(text):
            for rx, why in PERSONAL_MARKERS:
                if rx.search(line):
                    issues.append(f"{path}: personal ({why}): {line.strip()[:70]}")
                    break
    return issues


def check_contradictions(ctx: dict[str, str]) -> list[str]:
    issues = []
    for path, text in ctx.items():
        for line in content_lines(text):
            low = line.lower()
            if "skip tests" in low or "skip the tests" in low:
                issues.append(f"{path}: contradicts 'every model needs tests': {line.strip()[:70]}")
            if re.search(r"(--target[ =]prod|-t prod)", low) and not re.search(r"\b(never|don't|do not|blocked)\b", low):
                issues.append(f"{path}: contradicts 'never run against prod': {line.strip()[:70]}")
    return issues


STALE = [
    (re.compile(r"dev_wh", re.I), "stale name — the dev database is set in profiles.yml"),
    (re.compile(r"python 3\.10", re.I), "stale — pyproject.toml requires >=3.11"),
    (re.compile(r"\bQ[1-4]\b|migrating|roadmap", re.I), "a plan, not a fact"),
]


def check_stale(ctx: dict[str, str]) -> list[str]:
    issues = []
    for path, text in ctx.items():
        for line in content_lines(text):
            for rx, why in STALE:
                if rx.search(line):
                    issues.append(f"{path}: {why}: {line.strip()[:70]}")
                    break
    return issues


def check_budget(ctx: dict[str, str]) -> list[str]:
    n = len(content_lines(ctx.get("AGENTS.md", "")))
    if "AGENTS.md" not in ctx:
        return ["AGENTS.md does not exist yet"]
    return [] if n <= TEAM_BUDGET else [f"AGENTS.md has {n} lines, budget is {TEAM_BUDGET} — it's a map, not an encyclopedia"]


NUMBERED = re.compile(r"^\s*\d+[.)]\s")


def check_skill(ctx: dict[str, str]) -> list[str]:
    issues = []
    skill = ctx.get("skills/add-model/SKILL.md")
    if skill is None:
        issues.append("skills/add-model/SKILL.md does not exist — the 'Adding a model' procedure belongs in a skill")
    else:
        if not re.match(r"^---\n.*?\bname:.*?\bdescription:.*?\n---", skill, re.S):
            issues.append("skills/add-model/SKILL.md needs frontmatter with name: and description:")
        if sum(1 for l in content_lines(skill) if NUMBERED.match(l)) < 5:
            issues.append("skills/add-model/SKILL.md should contain the step-by-step checklist")
    for path, text in ctx.items():
        if path.endswith("AGENTS.md") and sum(1 for l in content_lines(text) if NUMBERED.match(l)) >= 5:
            issues.append(f"{path}: still contains a long numbered procedure — move it to the skill")
    return issues


def check_monolith(ctx: dict[str, str]) -> list[str]:
    text = ctx.get("CLAUDE.md")
    if text is None:
        return []
    rest = [l for l in content_lines(text) if not l.strip().startswith(("@", "<!--", "#")) and "AGENTS.md" not in l]
    if rest:
        return [f"CLAUDE.md still has {len(rest)} lines of its own — it should be empty or just point to AGENTS.md (e.g. '@AGENTS.md')"]
    return []


def check_precedence(ctx: dict[str, str]) -> list[str]:
    team = ctx.get("AGENTS.md", "")
    lines = [l.lower() for l in content_lines(team)]
    says_order = any(re.search(r"precedence|wins over|win over|overrides|takes priority", l) for l in lines)
    names_personal = any("personal" in l for l in lines)
    if says_order and names_personal:
        return []
    return ["AGENTS.md doesn't say which layer wins when team and personal notes disagree — so the agent decides"]


CHECKS = [
    ("Team layer holds no personal preferences", check_team_impersonal),
    ("No contradicting rules in any layer", check_contradictions),
    ("No stale facts or plans in agent context", check_stale),
    (f"AGENTS.md within budget ({TEAM_BUDGET} lines)", check_budget),
    ("Procedure lives in skills/add-model", check_skill),
    ("CLAUDE.md monolith is gone", check_monolith),
    ("Precedence between layers is explicit", check_precedence),
]


def main() -> int:
    ctx = context_files()
    passed = 0
    for title, fn in CHECKS:
        issues = fn(ctx)
        if issues:
            print(f"{RED}✗ {title}{RESET}")
            for i in issues[:6]:
                print(f"    {DIM}{i}{RESET}")
            if len(issues) > 6:
                print(f"    {DIM}… and {len(issues) - 6} more{RESET}")
        else:
            passed += 1
            print(f"{GREEN}✓ {title}{RESET}")
    colour = GREEN if passed == len(CHECKS) else RED
    print(f"\n{colour}{passed} of {len(CHECKS)}{RESET}")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
