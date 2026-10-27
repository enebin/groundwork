#!/usr/bin/env bash
# Prints the assignment for one app-method run (groundwork:ux-persona-reviewer) on one fixture.
# There is no headless iOS UI driver here, so a Claude Code session dispatches the reviewer as a
# subagent with this prompt and the iOS Simulator tools; see README.md.
# Usage: [BENCH_REPO=<repo>] app-prompt.sh <fixture-id> "<persona name>" <simulator-udid> <run-label>
set -euo pipefail

fixture=$1
persona=$2
udid=$3
label=$4

here=$(cd "$(dirname "$0")" && pwd)
plugin_root=$(cd "$here/../../../plugins/groundwork" && pwd)
worktrees=${BENCH_WORKTREES:-$HOME/.cache/groundwork-bench/ux-flow}
repo=${BENCH_REPO:-$worktrees/fixtures-repo}
mkdir -p "$(dirname "$repo")"
# Parallel first runs would otherwise see .git before the fetch finishes and miss the branches.
until mkdir "$repo.lock" 2>/dev/null; do sleep 1; done
trap 'rmdir "$repo.lock" 2>/dev/null || true' EXIT
if [ ! -d "$repo/.git" ]; then
  git init -q "$repo"
  git -C "$repo" fetch -q "$here/fixtures.bundle" 'refs/heads/*:refs/heads/*'
fi

key() { jq -r --arg f "$fixture" ".fixtures[] | select(.id == \$f) | .$1" "$here/answer-key.json"; }
branch=$(key branch)
worktree="$worktrees/$fixture"
if [ ! -d "$worktree" ]; then
  git -C "$repo" worktree add -q --detach "$worktree" "$branch"
fi
rmdir "$repo.lock"; trap - EXIT

base_sha=$(git -C "$repo" rev-parse --short "$(key base)")
subject=$(git -C "$repo" log -1 --format=%s "$branch")
goal=$(awk -v p="$persona" '$0 ~ "name: \"" p "\"" {getline; sub(/^ *goal: /, ""); print; exit}' "$worktree/GROUNDWORK.md")
device=$(xcrun simctl list devices | grep "$udid" | sed -E 's/^ *(.*) \(.*\) \(.*\) *$/\1/')
artifacts="$here/runs/$label/$fixture-$(echo "$persona" | tr 'A-Z ' 'a-z-')"
mkdir -p "$artifacts"

cat <<PROMPT
Plugin root: $plugin_root

Effort mode: normal. Scope: the tasks of your persona that this change touches.

Persona: $persona
Goal: $goal
(No \`## Persona\` section exists in GROUNDWORK.md.)

Target:
- Worktree: $worktree (detached HEAD, clean)
- Change under review: \`git diff $base_sha --\` ("$subject")
- Requirements: only the commit subject above. No design source exists; judge against the persona goal and iOS conventions.
- Affected screens: $(key screens).
- Known evidence: none. No UI test screenshots exist for this build.

Environment (yours alone):
- Simulator: $device, UDID $udid, already booted. The app has been uninstalled, so it starts with no data. Other simulators may be running for other reviewers. Pass this UDID explicitly on every simulator tool call; a call without it may land on another reviewer's device.
- Build it from the worktree yourself. Project: $worktree/WaterLog.xcodeproj, scheme WaterLog. The iOS Simulator tools \`mcp__Claude_Code_iOS_Simulator__build\` and \`mcp__Claude_Code_iOS_Simulator__control\` are available as deferred tools; load them with ToolSearch. You may also use xcodebuild and xcrun simctl.
- Artifact directory for screenshots and notes: $artifacts
- Test access: none needed. Use synthetic data only.

Do not modify any file in the worktree. Report as reference/rendered-review.md says.
PROMPT
