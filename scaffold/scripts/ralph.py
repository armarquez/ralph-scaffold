#!/usr/bin/env python3
"""Ralph loop runner: calls an agent CLI repeatedly until all tasks are done."""

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def _load_config(path: Path) -> dict:
    if not path.exists():
        print(f"error: .ralphrc.json not found at {path}", file=sys.stderr)
        print("Run from a directory containing .ralphrc.json.", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        print(f"error: invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def _task_runner_next(prd_file: str) -> dict:
    env = {**os.environ, "RALPH_PRD": prd_file}
    runner = Path(__file__).parent / "task_runner.py"
    result = subprocess.run(
        [sys.executable, str(runner), "next"],
        capture_output=True, text=True, env=env,
    )
    if result.returncode != 0:
        print(f"error: task_runner.py next failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def _git_changed_files(cwd: Path) -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f]


def _append_progress(progress_file: Path, task_id: str, outcome: str, notes: str = "") -> None:
    ts = datetime.now(UTC).isoformat(timespec="seconds")
    entry = f"\n## {ts} - {task_id} - {outcome}\n"
    if notes:
        entry += f"- {notes}\n"
    entry += "---\n"
    with progress_file.open("a") as f:
        f.write(entry)


def cmd_status(config: dict, loop_count: int, cb_state: str, last_task: str) -> None:
    print(f"loop_count:       {loop_count}")
    print(f"circuit_breaker:  {cb_state}")
    print(f"last_task:        {last_task or '(none)'}")
    print(f"max_loops:        {config.get('max_loops', 20)}")


def run_loop(config: dict, dry_run: bool) -> None:
    agent_cmd = config["agent_cmd"]
    prd_file = config.get("prd_file", "prd.json")
    prompt_file = Path(config.get("prompt_file", ".ralph/PROMPT.md"))
    progress_file = Path(config.get("progress_file", "progress.txt"))
    max_loops = config.get("max_loops", 20)
    cb_config = config.get("circuit_breaker", {})
    no_progress_threshold = cb_config.get("no_progress_threshold", 3)
    same_error_threshold = cb_config.get("same_error_threshold", 5)

    cwd = Path.cwd()
    loop_count = 0
    no_progress_streak = 0
    same_error_streak = 0
    last_error: str | None = None
    last_task = ""

    while loop_count < max_loops:
        task_info = _task_runner_next(prd_file)

        if task_info.get("done"):
            print(f"All tasks complete after {loop_count} loops.")
            _append_progress(progress_file, "ALL", "COMPLETE", "All non-optional tasks passed.")
            sys.exit(0)

        if task_info.get("blocked"):
            print("All remaining tasks are blocked. Halting.")
            _append_progress(progress_file, "ALL", "BLOCKED", "No runnable tasks remain.")
            sys.exit(2)

        task_id = task_info["id"]
        task_title = task_info["title"]
        last_task = task_id
        loop_count += 1

        print(f"\n[loop {loop_count}/{max_loops}] Task: {task_id} — {task_title}")

        prompt_context = ""
        if prompt_file.exists():
            prompt_context = prompt_file.read_text()

        if dry_run:
            print(f"  [dry-run] would run: {agent_cmd}")
            print(f"  [dry-run] prompt_file: {prompt_file}")
            _append_progress(progress_file, task_id, "DRY_RUN")
            no_progress_streak = 0
            continue

        files_before = set(_git_changed_files(cwd))

        agent_result = subprocess.run(
            agent_cmd, shell=True, capture_output=True, text=True,
            input=prompt_context,
        )

        files_after = set(_git_changed_files(cwd))
        new_changes = files_after - files_before

        if not new_changes and files_after == files_before:
            no_progress_streak += 1
        else:
            no_progress_streak = 0

        stderr_output = (agent_result.stderr or "").strip()
        if stderr_output:
            if stderr_output == last_error:
                same_error_streak += 1
            else:
                same_error_streak = 0
                last_error = stderr_output
        else:
            same_error_streak = 0
            last_error = None

        outcome = "PASS" if agent_result.returncode == 0 else "FAIL"
        _append_progress(progress_file, task_id, outcome)

        if no_progress_streak >= no_progress_threshold:
            msg = f"Circuit breaker: no file changes for {no_progress_streak} consecutive loops."
            print(f"\n[halt] {msg}")
            _append_progress(progress_file, task_id, "BLOCKED", msg)
            sys.exit(2)

        if same_error_streak >= same_error_threshold:
            msg = f"Circuit breaker: same error repeated {same_error_streak} times."
            print(f"\n[halt] {msg}")
            _append_progress(progress_file, task_id, "BLOCKED", msg)
            sys.exit(2)

    print(f"Max loops ({max_loops}) reached without completion.")
    _append_progress(progress_file, last_task, "BLOCKED", f"Hit max_loops={max_loops}.")
    sys.exit(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ralph loop runner")
    parser.add_argument("--dry-run", action="store_true", help="Print commands; skip agent call")
    parser.add_argument("--status", action="store_true", help="Print current state and exit")
    parser.add_argument("--config", default=".ralphrc.json", help="Path to .ralphrc.json")
    args = parser.parse_args()

    config = _load_config(Path(args.config))

    if args.status:
        cmd_status(config, loop_count=0, cb_state="closed", last_task="")
        return

    run_loop(config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
