#!/usr/bin/env bash
# Every failure exits quietly: a Stop hook must never get in the way.

cache="${XDG_CACHE_HOME:-$HOME/.cache}/groundwork"
stamp="$cache/last-check"
notified="$cache/notified-version"
latest_url="https://raw.githubusercontent.com/enebin/groundwork/main/plugins/groundwork/.claude-plugin/plugin.json"

read_version() {
  sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1
}

# Stop runs after every response, so the network is touched at most once a day.
if [ -n "$(find "$stamp" -mtime -1 2>/dev/null)" ]; then
  exit 0
fi
mkdir -p "$cache" && touch "$stamp" || exit 0

installed=$(read_version < "$CLAUDE_PLUGIN_ROOT/.claude-plugin/plugin.json")
latest=$(curl -fsS --max-time 2 "$latest_url" 2>/dev/null | read_version)

if [ -z "$installed" ] || [ -z "$latest" ]; then
  exit 0
fi
# A dev build or a rolled-back main can leave the installed version ahead.
if [ "$(printf '%s\n%s\n' "$installed" "$latest" | sort -V | tail -n 1)" = "$installed" ]; then
  exit 0
fi
if [ "$latest" = "$(cat "$notified" 2>/dev/null)" ]; then
  exit 0
fi
echo "$latest" > "$notified"

printf '{"systemMessage": "groundwork %s is available (installed: %s). Run `claude plugin update groundwork@groundwork`, then restart Claude Code."}\n' "$latest" "$installed"
