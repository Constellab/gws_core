#!/bin/bash
# Claude Code status line - shows cwd, model, context window usage and session cost.
# Receives the session JSON on stdin (see the `statusLine` command contract).

input=$(cat)

# Pull a numeric field out of the JSON (first match wins).
num() {
  local v
  v=$(printf '%s' "$input" | grep -o "\"$1\":[0-9.]*" | head -1)
  printf '%s' "${v##*:}"
}

# Pull a string field out of the JSON (first match wins).
str() {
  local v
  v=$(printf '%s' "$input" | grep -o "\"$1\":\"[^\"]*\"" | head -1)
  v=${v#*:\"}
  printf '%s' "${v%\"}"
}

used=$(num total_input_tokens)
size=$(num context_window_size)
cost=$(num total_cost_usd)
model=$(str display_name)
dir=$(str current_dir)

[ -n "$used" ] || used=0
[ -n "$size" ] || size=0
[ -n "$cost" ] || cost=0

# Human-readable token counts: 152.3k, 1.0M
human() {
  awk -v n="$1" 'BEGIN{
    if (n >= 1000000) printf "%.1fM", n/1000000;
    else if (n >= 1000) printf "%.1fk", n/1000;
    else printf "%d", n;
  }'
}

# Reset / dim / cyan
R=$'\033[0m'; DIM=$'\033[2m'; CYAN=$'\033[36m'

ctx=""
if [ "$size" -gt 0 ]; then
  pct=$(( used * 100 / size ))
  # green under 50%, yellow under 80%, red above
  if   [ "$pct" -lt 50 ]; then col=$'\033[32m'
  elif [ "$pct" -lt 80 ]; then col=$'\033[33m'
  else                         col=$'\033[31m'
  fi
  ctx="${DIM}ctx ${R}${col}$(human "$used")${DIM}/$(human "$size") (${pct}%)${R}"
fi

cost_fmt=$(awk -v c="$cost" 'BEGIN{printf "$%.4f", c}')

printf '%s%s%s %s|%s %s%s%s %s|%s %s %s|%s %s%s%s' \
  "$CYAN" "$(basename "$dir")" "$R" \
  "$DIM" "$R" \
  "$DIM" "$model" "$R" \
  "$DIM" "$R" \
  "$ctx" \
  "$DIM" "$R" \
  "$DIM" "$cost_fmt" "$R"
