# AGENTS.md — ralph-scaffold

## Build Commands

```bash
# First time setup (installs deps + wires pre-commit hook)
just install

# Run tests
just test

# Run linter
just lint

# Run both — required before every commit
just check

# Dry-run the ralph loop
just ralph

# Show task status
just status
```

Requires `mise` and `just`. Install mise once: `curl https://mise.run | sh`, then `mise install`.

## How to Run the Project

```bash
# Run the task runner against this repo's own prd.json
just status

# Run the loop runner in dry-run mode
just ralph

# Install scaffold into another project
./install.sh /path/to/target-project
```

## Key File Locations

| Path | Purpose |
|------|---------|
| `prd.json` | Machine-readable task list for this repo |
| `progress.txt` | Append-only loop log |
| `.ralph/PROMPT.md` | Agent instructions (this file's sibling) |
| `scaffold/` | Files that get copied into target projects |
| `scaffold/scripts/task_runner.py` | Task state machine (stdlib only) |
| `scaffold/scripts/ralph.py` | Loop runner (stdlib only) |
| `scaffold/hooks/pre-commit` | Git hook template |
| `tests/` | pytest test suite |

## Codebase Patterns

- **Stdlib only** in `scaffold/scripts/ralph.py` and `scaffold/scripts/task_runner.py`.
  No third-party imports; zero install friction when dropped into a target project.
- **RALPH_PRD env var** controls which prd.json file task_runner.py reads.
  Always set it when running task_runner.py against this repo's own prd.json.
- **Tests load scripts via importlib** to avoid making them installable packages.
  See `tests/test_task_runner.py:load_task_runner()` for the pattern.
- **Scripts exit with code 2** on circuit-breaker halt; code 1 on error; code 0 on success.
