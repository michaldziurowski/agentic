#!/usr/bin/env bash
# Claude Code status line — single line:
#   <path relative to $HOME> · <git branch> · 🧠 <tokens>/<window> · 💰 <cost>
#   · 5h <bar> <usage%> · 7d <bar> <usage%>
# Reads the session JSON from stdin (schema: https://code.claude.com/docs/en/statusline).

input=$(cat)

# Pull everything jq can give us in one pass (tab-separated). -1 marks absent
# rate-limit windows (only populated for Claude.ai Pro/Max after the first response).
IFS=$'\t' read -r DIR PCT COST USED WIN FIVEH SEVEND < <(
  jq -r '[
    (.workspace.current_dir // .cwd // ""),
    (.context_window.used_percentage // 0),
    (.cost.total_cost_usd // 0),
    (.context_window.total_input_tokens // 0),
    (.context_window.context_window_size // 200000),
    (.rate_limits.five_hour.used_percentage // -1),
    (.rate_limits.seven_day.used_percentage // -1)
  ] | @tsv' <<<"$input"
)

# Path relative to $HOME.
case "$DIR" in
  "$HOME")   REL="~" ;;
  "$HOME"/*) REL="~${DIR#"$HOME"}" ;;
  *)         REL="$DIR" ;;
esac

# Git branch (empty when not a repo); fall back to short SHA on detached HEAD.
BRANCH=$(git -C "$DIR" branch --show-current 2>/dev/null)
[ -z "$BRANCH" ] && BRANCH=$(git -C "$DIR" rev-parse --short HEAD 2>/dev/null)

PCT_INT=$(printf '%.0f' "$PCT")
COST_FMT=$(printf '$%.2f' "$COST")
FIVEH_INT=$(printf '%.0f' "$FIVEH")
SEVEND_INT=$(printf '%.0f' "$SEVEND")

human() {
  awk -v n="$1" 'BEGIN{
    if (n >= 1000000)   { v=n/1000000; if (v==int(v)) printf "%dM", v; else printf "%.1fM", v }
    else if (n >= 100000) printf "%.0fk", n/1000
    else if (n >= 1000)   { v=n/1000; if (v==int(v)) printf "%dk", v; else printf "%.1fk", v }
    else                  printf "%d", n
  }'
}

# Colors via ANSI-C quoting so plain `echo` emits them literally and never
# reinterprets backslashes/percent signs that might appear in paths.
DIM=$'\033[2m'; CYAN=$'\033[36m'; GREEN=$'\033[32m'
YELLOW=$'\033[33m'; RED=$'\033[31m'; RESET=$'\033[0m'

# Threshold color for a usage percentage: green < 70, yellow 70–89, red >= 90.
pct_color() {
  if   [ "$1" -ge 90 ]; then printf '%s' "$RED"
  elif [ "$1" -ge 70 ]; then printf '%s' "$YELLOW"
  else                       printf '%s' "$GREEN"
  fi
}

BAR_WIDTH=10

# "<label> <bar> <pct>%" — filled blocks threshold-colored, empty blocks dim.
usage_seg() {
  local label=$1 pct=$2 color filled empty fill pad
  color=$(pct_color "$pct")
  filled=$(( pct * BAR_WIDTH / 100 ))
  [ "$filled" -gt "$BAR_WIDTH" ] && filled=$BAR_WIDTH
  [ "$filled" -lt 0 ] && filled=0
  empty=$(( BAR_WIDTH - filled ))
  printf -v fill '%*s' "$filled" ''
  printf -v pad  '%*s' "$empty"  ''
  printf '%s %s%s%s%s%s %s%d%%%s' \
    "$label" "$color" "${fill// /█}" "$DIM" "${pad// /░}" "$RESET" "$color" "$pct" "$RESET"
}

SEP="${DIM} · ${RESET}"
line="${CYAN}${REL}${RESET}"
[ -n "$BRANCH" ] && line+="${SEP}${GREEN}${BRANCH}${RESET}"
line+="${SEP}🧠 $(pct_color "$PCT_INT")$(human "$USED")/$(human "$WIN")${RESET}"
line+="${SEP}💰 ${YELLOW}${COST_FMT}${RESET}"

usage=""
[ "$FIVEH_INT" -ge 0 ] && usage+="$(usage_seg 5h "$FIVEH_INT")"
if [ "$SEVEND_INT" -ge 0 ]; then
  [ -n "$usage" ] && usage+="$SEP"
  usage+="$(usage_seg 7d "$SEVEND_INT")"
fi
[ -n "$usage" ] && line+="${SEP}${usage}"

echo "$line"
