#!/usr/bin/env bash
# Starts one isolated Taskfold server per session: its own port, data directory, and host name.
# Usage: session.sh <run-label> <session-id> <port> [checkpoint]
#   With "workspace" as the checkpoint, the session starts from a signed-up owner with an organization
#   (owner lead-<run-label>@example.test, password studio2024x); open /dev/login?email=<owner> in the
#   participant's browser as setup.
set -euo pipefail

label=$1
id=$2
port=$3
checkpoint=${4:-}

here=$(cd "$(dirname "$0")" && pwd)
root=${BENCH_WORKTREES:-$HOME/.cache/groundwork-bench/ux-journey}
app="$root/taskfold"
data="$root/runs/$label/$id"
host="$id.localhost"
base="http://$host:$port"

if curl -s -o /dev/null "$base/"; then
  echo "Port $port already serves something; stop it first." >&2
  exit 1
fi
rm -rf "$data"
mkdir -p "$data"
PORT=$port DATA_DIR=$data PUBLIC_URL=$base nohup node "$app/server.js" > "$data/server.log" 2>&1 &
pid=$!
echo $pid > "$data/server.pid"
for _ in $(seq 1 50); do
  curl -s -o /dev/null "$base/" && break
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "Server exited; see $data/server.log" >&2
    exit 1
  fi
  sleep 0.2
done
curl -fs -o /dev/null "$base/" || { echo "Server did not answer at $base" >&2; exit 1; }

if [ "$checkpoint" = workspace ]; then
  owner="lead-$label@example.test"
  jar="$data/seed-cookies"
  curl -fsS -o /dev/null -d "name=Alex Kim&email=$owner&password=studio2024x" "$base/signup"
  token=$(curl -s "$base/dev/inbox?to=$owner" | grep -o 'token=[a-f0-9]*' | head -1)
  curl -fsS -o /dev/null "$base/verify?$token"
  curl -fsS -o /dev/null -c "$jar" -d "email=$owner&password=studio2024x" "$base/signin"
  curl -fsS -o /dev/null -b "$jar" -d "name=Nine Studio&slug=nine-studio" "$base/onboarding/org"
  rm -f "$jar"
  DATA_DIR=$data node "$app/tools.js" save workspace > /dev/null
fi

echo "$id $base data=$data"
