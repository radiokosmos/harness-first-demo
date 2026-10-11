"""Presenter's terminal script: one step per Enter, so nothing is typed live.

    bin/stage act2            # step through stage/act2.txt
    bin/stage act2 --from 18  # start at the step for slide 18
    bin/stage act2 --auto     # run everything without waiting (rehearsal check)

stage/<act>.txt format, one directive per line:

    --- 18 · caption       a new step (slide number · what the audience sees)
    $ command              shown, then run live after Enter
    ! command              run silently (preparation)
    > path [head|tail N]   replay a recorded file (agents are slow; recordings are not)
    @ branch               git checkout the branch for this act
    # comment              ignored
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BOLD, DIM, CYAN, RESET = "\033[1m", "\033[2m", "\033[36m", "\033[0m"


def parse(path: Path) -> list[dict]:
    steps: list[dict] = []
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("--- "):
            num, _, caption = line[4:].partition("·")
            steps.append({"slide": num.strip(), "caption": caption.strip(), "actions": []})
            continue
        if not steps:
            steps.append({"slide": "", "caption": "", "actions": []})
        steps[-1]["actions"].append((line[0], line[2:].strip()))
    return steps


def wait(auto: bool) -> None:
    if auto:
        return
    try:
        input()
    except EOFError:
        pass


def typed(text: str, auto: bool) -> None:
    if auto:
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(0.008)
    print()


def replay(spec: str) -> None:
    parts = spec.split()
    path = ROOT / parts[0]
    lines = path.read_text(errors="replace").splitlines() if path.exists() else [f"(missing recording: {parts[0]})"]
    if len(parts) == 3 and parts[1] in ("head", "tail"):
        n = int(parts[2])
        lines = lines[:n] if parts[1] == "head" else lines[-n:]
    print(f"{DIM}── recorded: {parts[0]}{RESET}")
    print("\n".join(lines))


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    act, auto = args[0], "--auto" in args
    start = args[args.index("--from") + 1] if "--from" in args else None
    path = ROOT / "stage" / f"{act}.txt"
    if not path.exists():
        print(f"no stage script {path.relative_to(ROOT)}; have: {', '.join(p.stem for p in sorted((ROOT / 'stage').glob('*.txt')))}")
        return 2
    steps = parse(path)
    if start:
        steps = steps[next((i for i, s in enumerate(steps) if s["slide"] == start), 0):]
    failed = 0
    for step in steps:
        if step["slide"] or step["caption"]:
            print(f"\n{CYAN}── slide {step['slide']} · {step['caption']}{RESET}")
        for kind, text in step["actions"]:
            sys.stdout.flush()
            if kind == "@":
                subprocess.run(["git", "checkout", "-q", text], cwd=ROOT, check=False)
                print(f"{DIM}(on branch {text}){RESET}")
            elif kind == "!":
                subprocess.run(text, shell=True, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            elif kind == "$":
                sys.stdout.write(f"{BOLD}$ {RESET}")
                typed(text, auto)
                wait(auto)
                sys.stdout.flush()
                rc = subprocess.run(text, shell=True, cwd=ROOT).returncode
                failed += auto and rc not in (0, 1)
            elif kind == ">":
                wait(auto)
                replay(text)
        wait(auto)
    print(f"\n{DIM}── end of {act}{RESET}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
