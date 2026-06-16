# PRD: ralph-scaffold

> **Agent instruction**: This is the source of truth. Read it fully before writing any code.
> Do not modify this file. Use TASKS.md as your live work board.

---

## 1. Project Identity

| Field | Value |
|---|---|
| **Project name** | `ralph-scaffold` |
| **Version** | `0.1.0` |
| **Status** | `active` |
| **Last updated** | `2026-06-15` |
| **Owner** | User |

---

## 2. Problem Statement

Developers using autonomous AI coding agents (OpenHands, Claude Code, Amp) need a
reusable project scaffold that enforces the Ralph loop methodology structurally —
not through prompts alone. Existing Ralph implementations are hardwired to specific
CLIs (Claude Code or Amp) and cannot be adopted without forking and gutting them.

This repo provides a tool-agnostic scaffold: a set of files, templates, and a
lightweight Python loop runner that any agent can use. A developer runs one install
command to drop the scaffold into any new project, then hands it to their agent of
choice.

---

## 3. Goals

- [ ] **G-01**: `install.sh` copies scaffold files into a target project in under 5 seconds
- [ ] **G-02**: `task_runner.py` can parse `prd.json`, return the next incomplete task, mark tasks complete/blocked, and exit when all tasks are done
- [ ] **G-03**: `ralph.py` runs a configurable loop calling an external agent CLI, reads task state, enforces exit gate, and respects max-loop and circuit-breaker limits
- [ ] **G-04**: All scaffold template files are populated with clear inline instructions so a human can fill them in without reading docs
- [ ] **G-05**: A pre-commit git hook blocks commits when tests fail
- [ ] **G-06**: The repo itself is self-hosting: its own `.ralph/` folder, `prd.json`, and `progress.txt` are valid examples of the scaffold in use

---

## 4. Non-Goals (Out of Scope for v0.1)

- No GUI or web dashboard
- No native Amp or Claude Code session management (tool-agnostic only)
- No GitHub issue integration
- No multi-project queue processing
- No tmux integration
- No Windows support (macOS + Linux only)
- No Docker runtime (scaffold runs on host; the *target project* may use Docker)

---

## 5. Tech Stack

| Layer | Choice | Notes |
|---|---|---|
| **Language** | Python 3.11+ | Loop runner and task runner only |
| **Shell** | Bash | install.sh and git hooks only |
| **Config format** | JSON | `prd.json`, `.ralphrc.json` |
| **Memory format** | Plaintext Markdown | `progress.txt`, `AGENTS.md`, `PROMPT.md` |
| **Testing** | pytest | All Python code requires tests |
| **Linting** | ruff | Must pass before any commit |
| **Package manager** | uv | For the scaffold repo itself |
| **External dependencies** | stdlib only | `ralph.py` and `task_runner.py` use no third-party packages |

---

## 6. Architecture Overview

```
ralph-scaffold/               # This repo (also a working example of itself)
│
├── install.sh                # Entry point: copies scaffold/ into a target project
│
├── scaffold/                 # Everything copied into target projects
│   ├── .ralph/
│   │   ├── PROMPT.md         # Agent instructions + EXIT_SIGNAL contract
│   │   ├── AGENTS.md         # Build/test/lint commands (agent fills this in)
│   │   └── specs/            # Empty dir; per-project detail goes here
│   ├── scripts/
│   │   ├── ralph.py          # Loop runner (calls agent CLI, checks exit gate)
│   │   └── task_runner.py    # prd.json state machine
│   ├── hooks/
│   │   └── pre-commit        # Git hook: blocks commits on test failure
│   ├── prd.json.example      # Annotated template; human renames to prd.json
│   ├── progress.txt          # Empty; agent appends each loop
│   └── .ralphrc.json         # Loop config: agent cmd, max loops, test cmd, etc.
│
├── tests/                    # Tests for ralph.py and task_runner.py
│   ├── test_task_runner.py
│   └── test_ralph.py
│
├── .ralph/                   # Scaffold's own Ralph state (self-hosting example)
│   ├── PROMPT.md
│   ├── AGENTS.md
│   └── specs/
│
├── prd.json                  # This project's own machine-readable PRD
├── progress.txt              # This project's own progress log
├── .ralphrc.json             # This project's own loop config
├── CLAUDE.md                 # Claude Code context file (points to AGENTS.md)
├── README.md
├── pyproject.toml
└── .gitignore
```

Key design decisions:

- **stdlib only for scripts**: `ralph.py` and `task_runner.py` import nothing outside
  Python stdlib. Zero install friction when dropped into a target project.
- **JSON for machine state, Markdown for human/agent prose**: `prd.json` is parsed
  by code; `PROMPT.md` and `progress.txt` are read by agents as context.
- **Self-hosting**: the scaffold repo uses its own scaffold. The `prd.json` at root
  IS the source of truth the loop runner reads. This validates the tooling works.
- **Tool-agnostic**: `ralph.py` shells out to whatever command is in `.ralphrc.json`.
  Swap `openai/claude-code` for `amp` or `gemini` with one config line change.

---

## 7. Data Models

### `prd.json` schema

```json
{
  "project": {
    "name": "string",
    "version": "string",
    "branch": "string"
  },
  "stories": [
    {
      "id": "string",          // e.g. "TASK-001"
      "title": "string",
      "priority": 1,           // integer, lower = higher priority
      "optional": false,       // if true, does not block completion
      "passes": false,         // set to true by agent when done
      "blocked": false,        // set to true by task_runner on failure
      "blocked_reason": "",    // error log when blocked
      "acceptance": "string",  // human-readable pass/fail condition
      "notes": ""
    }
  ]
}
```

### `.ralphrc.json` schema

```json
{
  "agent_cmd": "string",          // e.g. "claude --dangerously-skip-permissions"
  "test_cmd": "string",           // e.g. "pytest --tb=short -q"
  "lint_cmd": "string",           // e.g. "ruff check ."
  "max_loops": 20,
  "max_retries_per_task": 3,
  "circuit_breaker": {
    "no_progress_threshold": 3,   // open after N loops with no file changes
    "same_error_threshold": 5     // open after N loops with identical error
  },
  "prompt_file": ".ralph/PROMPT.md",
  "progress_file": "progress.txt",
  "prd_file": "prd.json"
}
```

### `progress.txt` entry format (agent-appended)

```
## [ISO datetime] - [TASK-ID] - [PASS|FAIL|BLOCKED]
- What was implemented
- Files changed: [comma-separated list]
- Learnings:
  - [pattern or gotcha discovered]
---
```

---

## 8. Acceptance Criteria

### install.sh
- [ ] `AC-01`: Running `./install.sh /path/to/target` copies all files from `scaffold/` into the target directory
- [ ] `AC-02`: Copies `hooks/pre-commit` into `target/.git/hooks/pre-commit` and makes it executable
- [ ] `AC-03`: Does not overwrite existing files (prompts or skips)
- [ ] `AC-04`: Prints a summary of what was copied

### task_runner.py
- [ ] `AC-05`: `python task_runner.py next` prints the highest-priority incomplete, non-blocked task ID and title as JSON
- [ ] `AC-06`: `python task_runner.py complete TASK-001` sets `passes: true` in `prd.json` and prints confirmation
- [ ] `AC-07`: `python task_runner.py block TASK-001 "error message"` sets `blocked: true` and writes `blocked_reason`
- [ ] `AC-08`: `python task_runner.py status` prints a summary table of all tasks and their state
- [ ] `AC-09`: `python task_runner.py next` exits with code `0` and prints `{"done": true}` when all non-optional tasks pass
- [ ] `AC-10`: Optional tasks (`"optional": true`) are excluded from completion check

### ralph.py
- [ ] `AC-11`: Reads `.ralphrc.json` on startup; fails fast with a clear error if missing
- [ ] `AC-12`: Each loop iteration: calls `task_runner.py next`, shells out to `agent_cmd` with `prompt_file` as context, then calls `task_runner.py` to check exit gate
- [ ] `AC-13`: Exits cleanly when `task_runner.py next` returns `{"done": true}`
- [ ] `AC-14`: Circuit breaker opens (loop halts) after `no_progress_threshold` consecutive loops with no git file changes
- [ ] `AC-15`: Circuit breaker opens after `same_error_threshold` consecutive loops with the same error string
- [ ] `AC-16`: On each loop, appends a `progress.txt` entry with task ID, outcome, and timestamp
- [ ] `AC-17`: `ralph.py --dry-run` prints what would be executed each loop without calling the agent
- [ ] `AC-18`: `ralph.py --status` prints current loop count, circuit breaker state, and last task

### pre-commit hook
- [ ] `AC-19`: Runs `test_cmd` from `.ralphrc.json`; blocks commit if exit code is non-zero
- [ ] `AC-20`: Prints a clear message identifying which test failed

### General
- [ ] `AC-21`: All pytest tests in `tests/` pass with zero failures
- [ ] `AC-22`: `ruff check .` returns no errors on all Python files
- [ ] `AC-23`: `ralph.py` and `task_runner.py` have no third-party imports
- [ ] `AC-24`: `README.md` contains a working quickstart that a new user can follow in under 10 minutes

---

## 9. Constraints & Environment

- **Python**: 3.11+ (uses `tomllib`, `match` statements)
- **OS**: macOS and Linux. No Windows.
- **External deps for scripts**: None (stdlib only). `pyproject.toml` dev deps for testing/linting are fine.
- **Git**: Target project must be a git repo (required for pre-commit hook and change detection)
- **No hardcoded paths**: all paths resolved relative to the project root or config file
- **No credentials**: nothing in any file touches API keys; the agent CLI handles auth

---

## 10. Open Questions

> Agent must not make assumptions about these. Flag and stop if encountered.

- [ ] Should `ralph.py` support a `--loop-once` flag for CI use (run exactly one iteration and exit)?
- [ ] Should `install.sh` run `git init` if the target directory is not already a git repo?
- [ ] Should `progress.txt` be committed to git or added to `.gitignore` by default?

---

## 11. Revision History

| Version | Date | Change |
|---|---|---|
| `0.1.0` | `2026-06-15` | Initial draft |
