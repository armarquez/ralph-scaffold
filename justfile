# ralph-scaffold justfile
# Run `just` to see all available recipes.

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
