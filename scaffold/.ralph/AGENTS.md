# AGENTS.md — [PROJECT NAME]

> **Fill in every [placeholder] before handing this file to an agent.**
> This file is your agent's build and navigation guide for this project.

---

## Build Commands

```bash
# Install dependencies
[INSTALL COMMAND]
# e.g. uv sync --extra dev

# Run tests
[TEST COMMAND]
# e.g. uv run pytest --tb=short -q

# Run linter
[LINT COMMAND]
# e.g. uv run ruff check .

# Run both (required before every commit)
[TEST COMMAND] && [LINT COMMAND]
```

---

## How to Run the Project Locally

```bash
# [Describe how to start the project]
# e.g. uv run python main.py
# e.g. npm run dev
```

---

## Key File Locations

| Path | Purpose |
|------|---------|
| `prd.json` | Machine-readable task list (do not edit manually) |
| `progress.txt` | Append-only loop log |
| `.ralph/PROMPT.md` | Agent instructions (this session's context) |
| `.ralph/specs/` | Per-task detail specs |
| `[MAIN SOURCE DIR]` | Primary source code |
| `[TEST DIR]` | Test files |

---

## Codebase Patterns

> **Agent fills this section in** after reading the codebase. Add patterns,
> conventions, and gotchas discovered during implementation.

- [Pattern 1: e.g. "All API calls go through src/api/client.py"]
- [Pattern 2: e.g. "Tests use pytest fixtures defined in tests/conftest.py"]
- [Pattern 3: e.g. "Config is loaded once at startup; never re-read mid-run"]
