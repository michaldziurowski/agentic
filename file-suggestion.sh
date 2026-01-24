#!/bin/bash
query=$(cat | jq -r '.query')

# Match both files and directories
fd --type f --type d --hidden 2>/dev/null | \
  fzf --filter="$query" | \
  head -15
