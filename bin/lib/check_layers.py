"""Act 1: is every line of agent context in the right layer?

    bin/check-layers

Seven checks. Run it as often as you like — it only reads files.
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


def sentences(text: str) -> list[str]:
    """Bullets and wrapped paragraphs, joined back up and split into sentences."""
    blocks, cur = [], []
    for line in content_lines(text):
        s = line.strip()
        if s.startswith(("#", "- ", "* ")) or NUMBERED.match(s):
            if cur:
                blocks.append(" ".join(cur))
            cur = [] if s.startswith("#") else [s.lstrip("-* ")]
        else:
            cur.append(s)
    if cur:
        blocks.append(" ".join(cur))
    return [x for b in blocks for x in re.split(r"(?<=[.;])\s+", b) if x.strip()]


# Which layer wins is the team's call, not the agent's. Asked only to make it
# explicit, every agent we ran wrote an order of its own: personal notes win on
# "workflow", personal notes win over the team, nobody stops on a conflict.
# This is what the team decided; change it by MR.
TEAM_DECISION = [
    ("team rules win over personal notes",
     re.compile(r"\b(team|this file|AGENTS\.md)\b.*\b(take[s]? precedence over|win[s]? over|override[s]?|beat[s]?)\b.*\bpersonal", re.I)),
    ("personal notes win only on how to talk to that person: language, tone, format of replies",
     re.compile(r"\bpersonal\b.*\bonly\b.*\b(talk|language|tone|repl(y|ies))|\bpersonal\b.*\b(talk|language|tone|repl(y|ies))\b.*\bonly\b", re.I)),
    ("if two instructions still conflict, stop and say so instead of choosing",
     re.compile(r"\b(conflict|disagree|contradict)\w*\b.*\b(stop|ask)|\b(stop|ask)\b.*\b(conflict|disagree|contradict)", re.I)),
]
OVER_TEAM = r"[^;]*?\b(take[s]? precedence over|win[s]? over|override[s]?|beat[s]?)\b[^;]*?\b(team|this file|AGENTS\.md|repo|project)\b"
PERSONAL_OVER_TEAM = re.compile(r"\bpersonal\b" + OVER_TEAM, re.I)
# in a personal file, "my notes" and "this file" are the personal layer too
MINE_OVER_TEAM = re.compile(r"\b(personal|my|mine|I|this file|these notes)\b" + OVER_TEAM, re.I)
PERSONAL_WINS = re.compile(r"\bpersonal\b[^;]*?\b(win[s]?|take[s]? precedence|override[s]?|set[s]?|decide[s]?)\b", re.I)
BEYOND_TALK = re.compile(r"\b(workflow|habit|process|how (you|they) work|tooling|tests?|data|safety)\b", re.I)


def check_precedence(ctx: dict[str, str]) -> list[str]:
    issues = []
    for path, text in ctx.items():
        for s in sentences(text):
            if (MINE_OVER_TEAM if path.startswith("people/") else PERSONAL_OVER_TEAM).search(s):
                issues.append(f"{path}: personal notes win over the team here: {s[:72]}")
            elif (m := PERSONAL_WINS.search(s)) and (b := BEYOND_TALK.search(s, m.end())) and not re.search(r"\b(never|not|don't)\b", s[m.end():b.start()], re.I):
                issues.append(f"{path}: personal notes win on {b.group(0)} here, not only on how to talk: {s[:60]}")
    team = sentences(ctx.get("AGENTS.md", ""))
    for what, rx in TEAM_DECISION:
        if not any(rx.search(s) for s in team):
            issues.append(f"AGENTS.md doesn't say what the team decided: {what}")
    return issues

CHECKS = [
    ("Team layer holds no personal preferences", check_team_impersonal),
    ("No contradicting rules in any layer", check_contradictions),
    ("No stale facts or plans in agent context", check_stale),
    (f"AGENTS.md within budget ({TEAM_BUDGET} lines)", check_budget),
    ("Procedure lives in skills/add-model", check_skill),
    ("CLAUDE.md monolith is gone", check_monolith),
    ("Precedence is written by the team", check_precedence),
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
