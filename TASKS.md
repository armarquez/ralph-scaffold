# TASKS.md — ralph-scaffold

> **Agent instruction**: This is your live work board. Read it at the start of every session.
> Work top-to-bottom through the Active Sprint only. Never skip ahead.
> Update status symbols as you work. Never delete a task — mark it `[x]` or `[!]`.
>
> **Loop protocol**:
> 1. Find the first `[ ]` task in Active Sprint.
> 2. Read its acceptance criteria in PRD.md before starting.
> 3. Implement it.
> 4. Run: `uv run pytest --tb=short -q && uv run ruff check .`
> 5. If passes → mark `[x]`, `git add -A && git commit -m "[TASK-ID] description"`, next task.
> 6. If fails → fix and retry (max 3 attempts), then mark `[!]` and log error in Notes.
> 7. After every commit, re-read this file before starting the next task.

---

## Status Key

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Complete |
| `[!]` | Blocked — see Notes |
| `[s]` | Skipped — deferred |

---

## Active Sprint: Repo Foundation + Core Scripts

---

### Phase 1 — Repo skeleton

- [ ] **TASK-001** — Initialize repo structure and pyproject.toml
  - Create all directories: `scaffold/.ralph/scaffold/.ralph/specs/`, `scaffold/scripts/`,
    `scaffold/hooks/`, `tests/`, `.ralph/specs/`
  - Create `pyproject.toml` with: `[project]` metadata, `[tool.ruff]` config,
    `[tool.pytest.ini_options]`, dev deps: `pytest`, `ruff`
  - Create `.gitignore` (Python standard: `__pycache__`, `.venv`, `*.pyc`, `dist/`)
  - Create empty placeholder files: `progress.txt`, `scaffold/progress.txt`
  - Acceptance: `uv run pytest` discovers `tests/` with zero errors; `uv run ruff check .` passes
  - Notes: —

- [ ] **TASK-002** — Write `prd.json` (this project's own machine-readable PRD)
  - Must conform exactly to the schema in PRD.md §7
  - Include all stories from this TASKS.md as entries (TASK-001 through TASK-015)
  - Set `passes: false` for all; set `optional: false` unless marked `[s]` above
  - Include the three Open Questions from PRD.md §10 as optional stories
  - Acceptance: `python -c "import json; json.load(open('prd.json'))"` exits 0
  - Notes: —

- [ ] **TASK-003** — Write `.ralphrc.json` (this project's own loop config)
  - Must conform exactly to the schema in PRD.md §7
  - Use `"agent_cmd": "claude --dangerously-skip-permissions"` as default
  - Use `"test_cmd": "uv run pytest --tb=short -q"` and `"lint_cmd": "uv run ruff check ."`
  - Acceptance: `python -c "import json; json.load(open('.ralphrc.json'))"` exits 0
  - Notes: —

---

### Phase 2 — task_runner.py

- [ ] **TASK-004** — Implement `task_runner.py` core (stdlib only)
  - Location: `scaffold/scripts/task_runner.py`
  - Subcommands: `next`, `complete <id>`, `block <id> <reason>`, `status`
  - `next`: reads `prd.json` (path from env var `RALPH_PRD` or default `prd.json`),
    returns highest-priority story where `passes=false` and `blocked=false` and `optional=false`
    as `{"id": "...", "title": "..."}`. If all done, returns `{"done": true}`.
  - `complete <id>`: sets `passes: true` for matching story, writes back to file
  - `block <id> <reason>`: sets `blocked: true`, writes `blocked_reason`, writes back to file
  - `status`: prints ASCII table of all stories with columns: ID | Title | Priority | Done | Blocked | Optional
  - All output is JSON except `status` which is plaintext table
  - Acceptance: AC-05 through AC-10 from PRD.md
  - Notes: —

- [ ] **TASK-005** — Write tests for task_runner.py
  - Location: `tests/test_task_runner.py`
  - Use `tmp_path` fixture to create temporary `prd.json` files
  - Test cases:
    - `next` returns highest priority incomplete task
    - `next` skips blocked tasks
    - `next` skips optional tasks for completion check
    - `next` returns `{"done": true}` when all non-optional tasks pass
    - `complete` mutates json correctly and is idempotent
    - `block` writes reason correctly
    - `status` runs without error
    - Missing `prd.json` raises clear error message
  - Acceptance: `uv run pytest tests/test_task_runner.py -v` exits 0
  - Notes: —

---

### Phase 3 — ralph.py loop runner

- [ ] **TASK-006** — Implement `ralph.py` core loop (stdlib only)
  - Location: `scaffold/scripts/ralph.py`
  - On startup: read `.ralphrc.json` (fail fast with clear error if missing or malformed)
  - Main loop:
    1. Call `task_runner.py next` — if `done`, print summary and exit 0
    2. Shell out to `agent_cmd` with `prompt_file` piped as stdin context
    3. Check git diff (`git diff --name-only HEAD`) to detect file changes
    4. Append entry to `progress_file`
    5. Increment loop counter; check `max_loops`
  - Flags: `--dry-run` (print what would run, don't call agent), `--status` (print state and exit)
  - Acceptance: AC-11 through AC-18 from PRD.md
  - Notes: —

- [ ] **TASK-007** — Implement circuit breaker in ralph.py
  - Track last N git diffs; if identical (no changes) for `no_progress_threshold` loops → halt
  - Track last N error outputs; if same string for `same_error_threshold` loops → halt
  - On halt: print circuit breaker state, log to `progress.txt`, exit with code 2
  - Acceptance: AC-14, AC-15 from PRD.md; unit test with mock subprocess
  - Notes: —

- [ ] **TASK-008** — Write tests for ralph.py
  - Location: `tests/test_ralph.py`
  - Mock `subprocess.run` for agent CLI calls
  - Test cases:
    - Reads `.ralphrc.json` correctly; missing file raises SystemExit with message
    - `--dry-run` prints expected commands without calling subprocess
    - Loop exits cleanly when `task_runner` returns `done: true`
    - Circuit breaker triggers correctly at threshold
    - `progress.txt` entry is appended on each loop
    - `max_loops` limit triggers graceful exit
  - Acceptance: `uv run pytest tests/test_ralph.py -v` exits 0
  - Notes: —

---

### Phase 4 — Scaffold template files

- [ ] **TASK-009** — Write `.ralph/PROMPT.md` template
  - Location: `scaffold/.ralph/PROMPT.md`
  - Must include:
    - Section 1: Agent role and project context (reads from `prd.json` and `progress.txt`)
    - Section 2: Loop protocol (read task → implement → test → commit → update prd.json)
    - Section 3: Required `RALPH_STATUS` output block format (EXIT_SIGNAL contract)
    - Section 4: What to do when blocked (max 3 retries, then call `task_runner.py block`)
    - Section 5: Code quality rules (no third-party deps without updating prd.json tech stack,
      tests required, lint must pass before commit)
  - The RALPH_STATUS block format:
    ```
    RALPH_STATUS:
      STATUS: WORKING | COMPLETE
      EXIT_SIGNAL: true | false
      TASK_ID: [current task id]
      TASKS_REMAINING: [integer]
      LAST_ACTION: [one sentence]
      BLOCKED: false | "reason string"
    ```
  - Acceptance: File exists; contains all 5 sections; RALPH_STATUS format is present verbatim
  - Notes: —

- [ ] **TASK-010** — Write `AGENTS.md` template and `prd.json.example`
  - `scaffold/.ralph/AGENTS.md`: template with clearly marked placeholders for:
    - Build command, test command, lint command
    - How to run the project locally
    - Key file locations
    - Codebase Patterns section (empty, agent fills in)
  - `scaffold/prd.json.example`: fully annotated example with inline comments as
    `"_comment_field"` sibling keys explaining each field's purpose
  - Acceptance: Both files exist and are valid (json.load passes on prd.json.example)
  - Notes: —

- [ ] **TASK-011** — Write `pre-commit` hook and `install.sh`
  - `scaffold/hooks/pre-commit`:
    - Reads `test_cmd` from `.ralphrc.json` using python (no jq dependency)
    - Runs test command; if exit code != 0, prints failing test output and exits 1
    - If `.ralphrc.json` missing, warns and allows commit (don't block non-ralph projects)
  - `install.sh`:
    - Usage: `./install.sh [target_dir]` (defaults to current directory)
    - Copies all files from `scaffold/` into target, preserving directory structure
    - For each file: if target exists, prompts user (overwrite/skip/abort)
    - Copies `hooks/pre-commit` → `target/.git/hooks/pre-commit`, sets executable
    - Prints summary: files copied, files skipped, next steps
    - Fails with clear error if target dir is not a git repo
  - Acceptance: AC-01 through AC-04, AC-19, AC-20 from PRD.md
  - Notes: —

---

### Phase 5 — Self-hosting wiring and docs

- [ ] **TASK-012** — Wire up self-hosting: populate `.ralph/` for this repo
  - `.ralph/PROMPT.md`: filled-in version using this repo's own prd.json
  - `.ralph/AGENTS.md`: filled-in with actual commands (`uv run pytest`, `uv run ruff check .`)
  - Validate: `python scaffold/scripts/task_runner.py status` runs against root `prd.json`
  - Acceptance: Running `task_runner.py status` from repo root prints correct task table
  - Notes: —

- [ ] **TASK-013** — Write `CLAUDE.md` (Claude Code context file)
  - Location: root `CLAUDE.md`
  - Content:
    - One-paragraph project summary
    - Pointer to `PRD.md` as source of truth
    - Pointer to `TASKS.md` as work board
    - Pointer to `.ralph/AGENTS.md` for build commands
    - Explicit instruction: "Read PRD.md and TASKS.md before writing any code"
  - Acceptance: File exists at root; contains all four pointers
  - Notes: —

- [ ] **TASK-014** — Write `README.md`
  - Sections: What is this, Prerequisites, Quickstart (3 steps), File reference table,
    How the loop works, Contributing
  - Quickstart must be testable end-to-end in under 10 minutes
  - Acceptance: AC-24 from PRD.md; all commands in Quickstart are syntactically valid
  - Notes: —

---

### Phase 6 — Final validation

- [ ] **TASK-015** — Full acceptance criteria sweep
  - Run through every AC in PRD.md §8 manually and verify
  - Run `uv run pytest --tb=short -q` → must exit 0
  - Run `uv run ruff check .` → must return "All checks passed"
  - Verify `ralph.py --dry-run` executes without errors
  - Verify `install.sh` works end-to-end into a fresh temp directory
  - Mark all passing stories `passes: true` in `prd.json`
  - Acceptance: All ACs checked; all prd.json stories pass; `task_runner.py next` returns `{"done": true}`
  - Notes: —

---

## Backlog (do not work on during this sprint)

- [ ] **TASK-B01** — `ralph.py --loop-once` flag for CI use
- [ ] **TASK-B02** — `install.sh` runs `git init` if target is not a git repo (resolve Open Question)
- [ ] **TASK-B03** — `progress.txt` gitignore decision (resolve Open Question)
- [ ] **TASK-B04** — GitHub Actions workflow running pytest + ruff on push
- [ ] **TASK-B05** — `task_runner.py import` command converts PRD.md → prd.json automatically
- [ ] **TASK-B06** — Support for `amp` agent cmd with autoHandoff config passthrough

---

## Discovered During Execution

*(agent adds tasks here mid-sprint; does not insert into Active Sprint mid-flight)*

---

## Blocked Tasks

*(paste blocked tasks here with full error log)*

---

## Completed Tasks

*(move completed tasks here for traceability)*

---

## Commit Log

*(agent appends one line per commit: `[TASK-ID] description (YYYY-MM-DD)`)*
