#!/bin/bash
query=$(cat | jq -r '.query')

FD=$(command -v fd || command -v fdfind)

# Match both files and directories
"$FD" --type f --type d --hidden 2>/dev/null | \
  fzf --filter="$query" | \
  head -15
