# TASKS.md — ralph-scaffold v0.2.0 (delta sprint)

> **Agent instruction**: v0.1.0 is complete. All 15 original tasks are done.
> This file contains ONLY the new work for v0.2.0: mise + just integration.
>
> **Before starting**: verify the baseline is clean:
> ```bash
> uv run pytest --tb=short -q   # must exit 0
> uv run ruff check .            # must return no errors
> ```
> If either fails, stop and report — do not proceed.
>
> **Loop protocol**:
> 1. Find the first `[ ]` task below.
> 2. Read its acceptance criteria in `PRD-v0.2.0.md` before starting.
> 3. Implement it.
> 4. Run: `uv run pytest --tb=short -q && uv run ruff check .`
> 5. If passes → mark `[x]`, commit, next task.
> 6. If fails → fix and retry (max 3 attempts), then mark `[!]` and log error.
> 7. After every commit, re-read this file before starting the next task.
>
> **Commit format**: `[TASK-1XX] brief description (v0.2.0)`

---

## Status Key

| Symbol | Meaning |
|---|---|
| `[ ]` | Not started |
| `[~]` | In progress |
| `[x]` | Complete |
| `[!]` | Blocked — see Notes |

---

## v0.2.0 Sprint: mise + just integration

---

### Phase A — Core tooling files (repo root)

- [x] **TASK-100** — Add v0.2.0 stories to `prd.json`
  - Append stories TASK-100 through TASK-107 to the `stories` array in `prd.json`
  - Each story: `passes: false`, `optional: false`, `blocked: false`
  - Use priorities 100–107
  - Do NOT modify any existing v0.1.0 story entries
  - Acceptance: `python -c "import json; d=json.load(open('prd.json')); assert any(s['id']=='TASK-107' for s in d['stories'])"` exits 0
  - Notes: —

- [x] **TASK-101** — Create `.mise.toml` at repo root
  - Content exactly as specified in `PRD-v0.2.0.md` §3
  - Tools: `python = "3.12"`, `uv = "latest"`, `just = "latest"`
  - Env: `UV_PYTHON = "python3.12"`
  - Acceptance: AC-100 from PRD-v0.2.0.md — file is valid TOML; `mise install` would succeed
    (validate by parsing with `python3 -c "import tomllib; tomllib.load(open('.mise.toml','rb'))"`)
  - Notes: —

- [x] **TASK-102** — Create `justfile` at repo root
  - Recipes: `install`, `test`, `lint`, `check`, `ralph`, `status`, `loop`
  - `install` recipe: runs `uv sync --extra dev`, copies pre-commit hook, prints `✓ installed`
  - `check` recipe: depends on `lint` then `test` (use `check: lint test` syntax)
  - `ralph` recipe: accepts variadic args, defaults to `--dry-run`
  - `status` recipe: sets `RALPH_PRD=prd.json` and calls task_runner.py
  - Acceptance: AC-101 through AC-106 from PRD-v0.2.0.md
  - Notes: Use `just` syntax (not Make). Tab indentation for recipe bodies. `@echo` suppresses command echo.

- [x] **TASK-103** — Update `CLAUDE.md` to use `just` verbs
  - Replace the "Build commands" section's raw `uv run ...` commands with `just` equivalents:
    - `just install` (first time setup)
    - `just check` (before every commit — lint + test)
    - `just test` (tests only)
    - `just lint` (lint only)
    - `just ralph` (dry-run loop)
    - `just loop` (full loop)
    - `just status` (task board)
  - Keep the Rules section unchanged
  - Acceptance: AC-111 from PRD-v0.2.0.md — all four `just` verbs present
  - Notes: —

---

### Phase B — Scaffold template updates

- [x] **TASK-104** — Add `scaffold/justfile.example` and `scaffold/.mise.toml.example`
  - `scaffold/justfile.example`: content from PRD-v0.2.0.md §5 — includes `# EDIT THIS` markers
    and `[PLACEHOLDERS]` for project-specific commands
  - `scaffold/.mise.toml.example`: content from PRD-v0.2.0.md §6 — includes `# EDIT THIS` markers
    and `# EDIT:` inline comments
  - Update `install.sh` to copy these two new files alongside the existing scaffold files
    (they live at `scaffold/justfile.example` and `scaffold/.mise.toml.example` so the existing
    `find "$SCAFFOLD_DIR" -type f ...` loop will pick them up automatically — verify this)
  - Acceptance: AC-107, AC-108 from PRD-v0.2.0.md; running `./install.sh /tmp/test-target` (in a fresh git repo) copies both files
  - Notes: The existing `install.sh` uses `find "$SCAFFOLD_DIR" -type f ...` — new files in `scaffold/` are picked up automatically. Verify by inspection rather than modifying `install.sh`.

- [x] **TASK-105** — Update `scaffold/hooks/pre-commit` to prefer `just check`
  - New logic (as specified in PRD-v0.2.0.md §7):
    1. If `justfile` or `Justfile` exists in the project root → run `just check`
    2. Else fall back to reading `test_cmd` from `.ralphrc.json`
    3. Else warn and allow commit
  - The existing fallback logic (reading `.ralphrc.json`) must remain intact and unchanged
  - Acceptance: AC-109, AC-110 from PRD-v0.2.0.md
  - Notes: Test the justfile branch by temporarily creating a `justfile` in a temp dir and running the hook. The fallback branch is already tested by the fact that it matches current behavior.

- [x] **TASK-106** — Update both `AGENTS.md` files to reference `just`
  - `.ralph/AGENTS.md` (this repo's filled-in file): replace raw `uv run pytest` and
    `uv run ruff check .` with `just test`, `just lint`, `just check`. Add `just install`
    to the install step. Keep the "Key File Locations" and "Codebase Patterns" sections unchanged.
  - `scaffold/.ralph/AGENTS.md` (the template): update the Build Commands section to show
    `just install`, `just test`, `just lint`, `just check` as the preferred idiom,
    with the raw commands shown as fallback examples in comments. Keep all `[PLACEHOLDER]` markers.
  - Acceptance: AC-112, AC-113 from PRD-v0.2.0.md
  - Notes: —

---

### Phase C — README consistency fix

- [x] **TASK-107** — Fix `README.md` inconsistencies and add mise/just to prerequisites
  - Prerequisites section: add `mise` (with install one-liner) and `just` (installed via mise)
    above the existing Python and uv entries. Note that `mise install` handles Python, uv, and just.
  - Quickstart Step 1: add `mise install` as the first sub-step before `./install.sh`
  - Quickstart Step 3 "Run the loop": replace raw `python scaffold/scripts/...` commands with
    `just status`, `just ralph`, `just loop` where appropriate. Keep raw python commands as
    fallback alternatives in a note.
  - Fix the `uv sync` vs `uv sync --extra dev` inconsistency — use `uv sync --extra dev`
    everywhere (matches `pyproject.toml`)
  - Acceptance: AC-114, AC-115 from PRD-v0.2.0.md
  - Notes: Do not change the "How the Loop Works" mermaid diagram or the File Reference table.

---

### Phase D — Final validation

- [x] **TASK-108** — Full v0.2.0 acceptance criteria sweep
  - Run through every AC-100 through AC-118 in `PRD-v0.2.0.md` §8 and verify each one
  - Run `uv run pytest --tb=short -q` → must exit 0 (no regressions)
  - Run `uv run ruff check .` → must return no errors
  - Run `just --list` → must show all recipes without error
  - Run `just check` → must pass (calls lint then test)
  - Run `just ralph` → must print dry-run output without error
  - Run `just status` → must print task table
  - Mark TASK-100 through TASK-107 as `passes: true` in `prd.json`
  - Verify `RALPH_PRD=prd.json python scaffold/scripts/task_runner.py next` returns a
    v0.2.0 task (TASK-100 through TASK-107) or `{"done": true}` if all pass
  - Acceptance: All ACs checked; `just check` exits 0; no regressions in existing tests
  - Notes: —

---

## Backlog (unchanged from v0.1.0 — do not work on these)

- [ ] **TASK-B01** — `ralph.py --loop-once` flag for CI use
- [ ] **TASK-B02** — `install.sh` runs `git init` if target is not a git repo
- [ ] **TASK-B03** — `progress.txt` gitignore decision
- [ ] **TASK-B04** — GitHub Actions workflow running pytest + ruff on push
- [ ] **TASK-B05** — `task_runner.py import` converts PRD.md → prd.json
- [ ] **TASK-B06** — Support for `amp` agent cmd with autoHandoff config

---

## Discovered During Execution

*(agent adds tasks here mid-sprint)*

---

## Blocked Tasks

*(none)*

---

## Commit Log (v0.2.0)

- [TASK-100/101/102] prd.json v0.2.0 stories, .mise.toml, justfile (2026-06-16)
- [TASK-103] update CLAUDE.md to use just verbs as primary commands (2026-06-16)
- [TASK-104/105] scaffold examples and updated pre-commit hook (2026-06-16)
- [TASK-106] update both AGENTS.md files to use just verbs (2026-06-16)
- [TASK-107] fix README with mise/just prerequisites and consistent uv sync (2026-06-16)
- [TASK-108] final v0.2.0 AC sweep — all tasks complete, prd.json done (2026-06-16)
