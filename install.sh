#!/usr/bin/env bash
# install.sh: copies scaffold/ into a target project directory.
# Usage: ./install.sh [target_dir]   (defaults to current directory)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCAFFOLD_DIR="$SCRIPT_DIR/scaffold"
TARGET_DIR="${1:-$PWD}"

if [ ! -d "$TARGET_DIR" ]; then
    echo "error: target directory does not exist: $TARGET_DIR" >&2
    exit 1
fi

if [ ! -d "$TARGET_DIR/.git" ]; then
    echo "error: $TARGET_DIR is not a git repository (.git not found)" >&2
    echo "hint: run 'git init' in the target directory first" >&2
    exit 1
fi

copied=0
skipped=0

copy_file() {
    local src="$1"
    local dst="$2"

    if [ -f "$dst" ]; then
        printf "  [exists] %s — overwrite? [y/N/a(bort)] " "$dst"
        read -r answer
        case "$answer" in
            y|Y) ;;
            a|A)
                echo "Aborted."
                exit 1
                ;;
            *)
                echo "  [skip]   $dst"
                skipped=$((skipped + 1))
                return
                ;;
        esac
    fi

    mkdir -p "$(dirname "$dst")"
    cp "$src" "$dst"
    echo "  [copy]   $dst"
    copied=$((copied + 1))
}

echo "Installing ralph-scaffold into: $TARGET_DIR"
echo ""

# Copy all files from scaffold/ preserving directory structure
while IFS= read -r -d '' src_file; do
    rel="${src_file#"$SCAFFOLD_DIR/"}"
    dst_file="$TARGET_DIR/$rel"
    copy_file "$src_file" "$dst_file"
done < <(find "$SCAFFOLD_DIR" -type f -not -name '__init__.py' -not -path '*/__pycache__/*' -not -name '*.pyc' -print0)

# Install pre-commit hook
HOOK_SRC="$SCAFFOLD_DIR/hooks/pre-commit"
HOOK_DST="$TARGET_DIR/.git/hooks/pre-commit"

echo ""
echo "Installing pre-commit hook..."

if [ -f "$HOOK_DST" ]; then
    printf "  [exists] %s — overwrite? [y/N] " "$HOOK_DST"
    read -r answer
    if [[ "$answer" =~ ^[yY]$ ]]; then
        cp "$HOOK_SRC" "$HOOK_DST"
        chmod +x "$HOOK_DST"
        echo "  [copy]   $HOOK_DST (executable)"
        copied=$((copied + 1))
    else
        echo "  [skip]   $HOOK_DST"
        skipped=$((skipped + 1))
    fi
else
    cp "$HOOK_SRC" "$HOOK_DST"
    chmod +x "$HOOK_DST"
    echo "  [copy]   $HOOK_DST (executable)"
    copied=$((copied + 1))
fi

echo ""
echo "Done. $copied file(s) copied, $skipped file(s) skipped."
echo ""
echo "Next steps:"
echo "  1. Rename prd.json.example → prd.json and fill it in"
echo "  2. Fill in .ralph/AGENTS.md with your build/test/lint commands"
echo "  3. Fill in .ralph/PROMPT.md with your project context"
echo "  4. Edit .ralphrc.json to set your agent_cmd"
echo "  5. Run: python scripts/ralph.py"
