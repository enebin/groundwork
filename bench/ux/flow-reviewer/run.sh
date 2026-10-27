#!/usr/bin/env bash
# Runs ux-flow-reviewer headlessly against one fixture branch from fixtures.bundle.
# Usage: [AGENT_FILE=<agent.md>] [BENCH_REPO=<repo with bench/* branches>] run.sh <fixture-id> <run-label> [model]
# The agent body is used as the system prompt, which mirrors how a subagent receives it,
# so the reviewer under test is always this checkout's version, not the installed plugin.
set -euo pipefail

fixture=$1
label=$2
model=${3:-claude-sonnet-5-5}

here=$(cd "$(dirname "$0")" && pwd)
plugin_root=$(cd "$here/../../../plugins/groundwork" && pwd)
branch=$(jq -r --arg f "$fixture" '.fixtures[] | select(.id == $f) | .branch' "$here/answer-key.json")
base_branch=$(jq -r --arg f "$fixture" '.fixtures[] | select(.id == $f) | .base' "$here/answer-key.json")
out_dir="$here/runs/$label"
# Worktrees stay outside this repository so its CLAUDE.md does not leak into the reviewer's context.
worktrees=${BENCH_WORKTREES:-$HOME/.cache/groundwork-bench/ux-flow}
mkdir -p "$out_dir" "$worktrees"

repo=${BENCH_REPO:-$worktrees/fixtures-repo}
# Parallel first runs would otherwise see .git before the fetch finishes and miss the branches.
until mkdir "$repo.lock" 2>/dev/null; do sleep 1; done
trap 'rmdir "$repo.lock" 2>/dev/null || true' EXIT
if [ ! -d "$repo/.git" ]; then
  git init -q "$repo"
  git -C "$repo" fetch -q "$here/fixtures.bundle" 'refs/heads/*:refs/heads/*'
fi

worktree="$worktrees/$fixture"
if [ ! -d "$worktree" ]; then
  git -C "$repo" worktree add -q --detach "$worktree" "$branch"
fi
rmdir "$repo.lock"; trap - EXIT

base_sha=$(git -C "$repo" rev-parse "$base_branch")
head_sha=$(git -C "$repo" rev-parse "$branch")
changed=$(git -C "$worktree" diff --name-status "$base_sha" "$head_sha")

system_prompt="$out_dir/.agent-body.md"
agent_file=${AGENT_FILE:-$plugin_root/agents/ux-flow-reviewer.md}
awk 'BEGIN{n=0} /^---$/ && n<2 {n++; next} n>=2' "$agent_file" > "$system_prompt"

prompt=$(cat <<EOF
Plugin root: $plugin_root

Selected personas and tasks: every \`user\` persona in GROUNDWORK.md — the tasks of each that the change touches.

Target: local (local changes against $base_branch)
Pinned refs: base $base_sha, head $head_sha, clean working tree
View the change: git diff $base_sha --
Read files: read files from the working tree
Changed files:
$changed

Read GROUNDWORK.md, the documents it names, and your own "## Review focus: ux" section.
Do not modify code. Use only read-only git commands.

$(awk '/^Reporting rules:/,/^- 🟡 Minor/' "$plugin_root/skills/review/SKILL.md")
EOF
)

cd "$worktree"
start=$(date +%s)
claude -p "$prompt" \
  --model "$model" \
  --system-prompt-file "$system_prompt" \
  --tools "Read,Grep,Glob,Bash" \
  --allowedTools "Read" "Grep" "Glob" \
    "Bash(git diff:*)" "Bash(git log:*)" "Bash(git show:*)" "Bash(git status:*)" \
    "Bash(ls:*)" "Bash(find:*)" "Bash(cat:*)" "Bash(head:*)" "Bash(sed:*)" "Bash(wc:*)" "Bash(grep:*)" \
  --strict-mcp-config \
  --settings '{"disableAllHooks": true}' \
  --no-session-persistence \
  --output-format stream-json --verbose \
  > "$out_dir/$fixture.jsonl" 2> "$out_dir/$fixture.stderr" || true
echo "$fixture $label done in $(( $(date +%s) - start ))s"
