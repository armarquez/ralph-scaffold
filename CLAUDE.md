# CLAUDE.md — ralph-scaffold

You are building `ralph-scaffold`: a tool-agnostic Ralph loop scaffold for autonomous
AI coding agents. Read the files below in order before writing any code.

## Read these first (in order)

1. **`PRD.md`** — source of truth: problem, goals, tech stack, architecture, acceptance criteria
2. **`TASKS.md`** — your live work board: what to build, in what order, and how to verify it

## Build commands

```bash
just install   # first time setup (installs deps + wires pre-commit hook)
just check     # before every commit (lint + tests)
just test      # tests only
just lint      # lint only
just ralph     # dry-run loop
just loop      # full loop (calls agent)
just status    # task status table
```

Requires `mise` and `just`. Install mise once: `curl https://mise.run | sh`, then `mise install`.

## Rules

- Work through TASKS.md top-to-bottom. Do not skip ahead.
- No third-party imports in `scaffold/scripts/ralph.py` or `scaffold/scripts/task_runner.py`.
- Every task requires passing tests before the commit (`just check`).
- If you hit an Open Question from PRD.md §10, stop and flag it. Do not guess.
- Append one line to the Commit Log in TASKS.md after each commit.
