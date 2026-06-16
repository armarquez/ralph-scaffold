# ralph-scaffold justfile

[private]
default:
    @just --list

# ── This repo ────────────────────────────────────────────────────────────────

# Install all dependencies and wire the pre-commit hook
install:
    uv sync --extra dev
    cp scaffold/hooks/pre-commit .git/hooks/pre-commit
    chmod +x .git/hooks/pre-commit
    @echo "✓ installed"

# Run tests
test:
    uv run pytest --tb=short -q

# Run linter
lint:
    uv run ruff check .

# Run lint then tests (required before every commit)
check: lint test

# Run the ralph loop against this repo (dry-run by default)
ralph *args="--dry-run":
    uv run python scaffold/scripts/ralph.py {{args}}

# Show current task status
status:
    RALPH_PRD=prd.json uv run python scaffold/scripts/task_runner.py status

# Run the full loop (not dry-run)
loop:
    uv run python scaffold/scripts/ralph.py

# ── Onboarding ───────────────────────────────────────────────────────────────

# Copy scaffold into a target project (defaults to current directory)
scaffold target=".":
    ./install.sh {{target}}

# Print the post-scaffold setup checklist for a target project
[no-cd]
setup target=".":
    @echo ""
    @echo "Next steps in {{target}}:"
    @echo ""
    @echo "  1. Pin your tools:"
    @echo "       cp .mise.toml.example .mise.toml  # then edit Python version if needed"
    @echo "       mise install"
    @echo ""
    @echo "  2. Set up the task runner:"
    @echo "       cp prd.json.example prd.json"
    @echo "       # Edit prd.json — add your project name and stories"
    @echo ""
    @echo "  3. Create your justfile:"
    @echo "       cp justfile.example justfile"
    @echo "       # Replace [PLACEHOLDERS] with your build/test/lint commands"
    @echo ""
    @echo "  4. Fill in agent context:"
    @echo "       # Edit .ralph/AGENTS.md — add your build commands"
    @echo "       # Edit .ralph/PROMPT.md — add your project description"
    @echo ""
    @echo "  5. Configure the loop:"
    @echo "       # Edit .ralphrc.json — set agent_cmd to your agent"
    @echo "       # e.g. claude --dangerously-skip-permissions"
    @echo ""
    @echo "  6. Run:"
    @echo "       just status    # verify task list"
    @echo "       just ralph     # dry-run to preview"
    @echo "       just loop      # start the loop"
    @echo ""

# Scaffold and print setup checklist in one step
onboard target:
    @just scaffold {{target}}
    @just setup {{target}}
