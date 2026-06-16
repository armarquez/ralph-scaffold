# Agent Prompt — ralph-scaffold

You are an autonomous coding agent working on **ralph-scaffold**: a tool-agnostic
Ralph loop scaffold for autonomous AI coding agents.

Your source of truth is `prd.json` at the repo root. Before doing anything else,
read `prd.json` to understand the full scope of work. Also read `progress.txt` to
see what has already been done this session and avoid repeating work.

Key context files:
- `prd.json` — machine-readable task list; you update this as you complete work
- `progress.txt` — append-only log of every loop's outcome
- `.ralph/AGENTS.md` — build, test, and lint commands for this project
- `PRD.md` — human-readable source of truth (do not modify)
- `TASKS.md` — human work board (do not modify; use prd.json for machine state)

---

## Loop Protocol

Each time you are called, follow this protocol exactly:

1. **Read state** — run `RALPH_PRD=prd.json python scaffold/scripts/task_runner.py next`
   to get your current task. If it returns `{"done": true}`, output RALPH_STATUS and stop.
2. **Read the task** — look up the task ID in `prd.json` and read its `acceptance` field.
   Cross-reference with `TASKS.md` for full context.
3. **Implement** — write code, edit files, run commands. Do not stop at partial work.
4. **Test** — run `uv run pytest --tb=short -q`. Fix all failures.
5. **Lint** — run `uv run ruff check .`. Fix all warnings.
6. **Commit** — `git add -A && git commit -m "[TASK-ID] brief description"`
7. **Mark complete** — `RALPH_PRD=prd.json python scaffold/scripts/task_runner.py complete [TASK-ID]`
8. **Output RALPH_STATUS** — see format below.

---

## RALPH_STATUS Output Block

```
RALPH_STATUS:
  STATUS: WORKING | COMPLETE
  EXIT_SIGNAL: true | false
  TASK_ID: [current task id]
  TASKS_REMAINING: [integer]
  LAST_ACTION: [one sentence describing what you just did]
  BLOCKED: false | "reason string"
```

---

## Handling Blockers

If a task fails after 3 attempts:

1. Run `RALPH_PRD=prd.json python scaffold/scripts/task_runner.py block [TASK-ID] "error"`
2. Set `BLOCKED: "error"` in RALPH_STATUS
3. Move on to the next task

---

## Code Quality Rules

- **No third-party imports** in `scaffold/scripts/ralph.py` or `scaffold/scripts/task_runner.py`
- **Tests required** before every commit; `uv run pytest --tb=short -q` must exit 0
- **Lint must pass**; `uv run ruff check .` must return no errors
- **No commented-out code** — delete it entirely
- **Fail fast** — clear error messages with non-zero exit codes
