#!/usr/bin/env bash
# Symlinks this repository's Claude Code configuration into ~/.claude.
set -euo pipefail

if ! command -v jq >/dev/null; then
    echo "error: jq is not installed (required by statusline.sh)" >&2
    exit 1
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
SELF="$REPO_DIR/$(basename "${BASH_SOURCE[0]}")"

link() {
    local src="$1" dst="$2"

    if [ -L "$dst" ]; then
        if [ "$(readlink -f "$dst")" = "$src" ]; then
            echo "ok      $dst"
            return
        fi
        rm "$dst"
    elif [ -e "$dst" ]; then
        echo "SKIP    $dst (exists and is not a symlink)" >&2
        return
    fi

    ln -s "$src" "$dst"
    echo "linked  $dst -> $src"
}

mkdir -p "$CLAUDE_DIR/skills"

link "$REPO_DIR/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
link "$REPO_DIR/settings.json" "$CLAUDE_DIR/settings.json"

for script in "$REPO_DIR"/*.sh; do
    [ -e "$script" ] || continue
    [ "$script" = "$SELF" ] && continue
    link "$script" "$CLAUDE_DIR/$(basename "$script")"
done

for skill in "$REPO_DIR"/skills/*/; do
    [ -d "$skill" ] || continue
    skill="${skill%/}"
    link "$skill" "$CLAUDE_DIR/skills/$(basename "$skill")"
done
