#!/usr/bin/env python3
"""Task runner for the Ralph loop: reads/writes prd.json state."""

import json
import os
import sys
from pathlib import Path


def _load_prd(prd_path: Path) -> dict:
    if not prd_path.exists():
        print(f"error: prd.json not found at {prd_path}", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(prd_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {prd_path}: {exc}", file=sys.stderr)
        sys.exit(1)


def _save_prd(prd_path: Path, data: dict) -> None:
    prd_path.write_text(json.dumps(data, indent=2) + "\n")


def _prd_path() -> Path:
    return Path(os.environ.get("RALPH_PRD", "prd.json"))


def cmd_next(args: list[str]) -> None:
    prd = _load_prd(_prd_path())
    stories = prd.get("stories", [])

    incomplete = [
        s for s in stories
        if not s.get("passes", False)
        and not s.get("blocked", False)
        and not s.get("optional", False)
    ]

    if not incomplete:
        all_required = [s for s in stories if not s.get("optional", False)]
        all_done = all(s.get("passes", False) for s in all_required)
        if all_done:
            print(json.dumps({"done": True}))
            return
        # All remaining are blocked — still signal done=false but no next task
        print(json.dumps({"done": False, "blocked": True}))
        return

    next_story = min(incomplete, key=lambda s: s.get("priority", 999))
    print(json.dumps({"id": next_story["id"], "title": next_story["title"]}))


def cmd_complete(args: list[str]) -> None:
    if not args:
        print("error: complete requires a task ID", file=sys.stderr)
        sys.exit(1)
    task_id = args[0]
    path = _prd_path()
    prd = _load_prd(path)

    for story in prd["stories"]:
        if story["id"] == task_id:
            story["passes"] = True
            _save_prd(path, prd)
            print(json.dumps({"ok": True, "id": task_id}))
            return

    print(f"error: task {task_id!r} not found", file=sys.stderr)
    sys.exit(1)


def cmd_block(args: list[str]) -> None:
    if len(args) < 2:
        print("error: block requires a task ID and reason", file=sys.stderr)
        sys.exit(1)
    task_id, reason = args[0], args[1]
    path = _prd_path()
    prd = _load_prd(path)

    for story in prd["stories"]:
        if story["id"] == task_id:
            story["blocked"] = True
            story["blocked_reason"] = reason
            _save_prd(path, prd)
            print(json.dumps({"ok": True, "id": task_id, "reason": reason}))
            return

    print(f"error: task {task_id!r} not found", file=sys.stderr)
    sys.exit(1)


def cmd_status(args: list[str]) -> None:
    prd = _load_prd(_prd_path())
    stories = prd.get("stories", [])

    col_id = max((len(s["id"]) for s in stories), default=2)
    col_title = max((len(s["title"]) for s in stories), default=5)
    col_id = max(col_id, 2)
    col_title = max(col_title, 5)

    header = (
        f"{'ID':<{col_id}}  {'Title':<{col_title}}  {'Pri':>3}  "
        f"{'Done':<4}  {'Blocked':<7}  {'Optional':<8}"
    )
    sep = "-" * len(header)
    print(header)
    print(sep)

    for s in sorted(stories, key=lambda x: x.get("priority", 999)):
        done = "yes" if s.get("passes") else "no"
        blocked = "yes" if s.get("blocked") else "no"
        optional = "yes" if s.get("optional") else "no"
        print(
            f"{s['id']:<{col_id}}  {s['title']:<{col_title}}  "
            f"{s.get('priority', 0):>3}  {done:<4}  {blocked:<7}  {optional:<8}"
        )


COMMANDS = {
    "next": cmd_next,
    "complete": cmd_complete,
    "block": cmd_block,
    "status": cmd_status,
}


def main() -> None:
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        cmds = ", ".join(COMMANDS)
        print(f"usage: task_runner.py <{cmds}> [args...]", file=sys.stderr)
        sys.exit(1)
    COMMANDS[args[0]](args[1:])


if __name__ == "__main__":
    main()
