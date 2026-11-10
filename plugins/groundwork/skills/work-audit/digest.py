#!/usr/bin/env python3
"""Summarize the agent sessions (Claude Code and Codex) run in one repository during a time range.

Usage: digest.py --repo <path> [--since TIME] [--until TIME]
TIME is ISO 8601, such as 2026-11-09 or 2026-11-09T07:00; without an offset it is local time.
--until defaults to now, --since to 24 hours before --until.

Only numbers and short excerpts go out, so the report agent never reads raw transcripts.
"""
import argparse, collections, functools, glob, json, os, re, subprocess, sys
from datetime import datetime, timedelta

IDLE_SECONDS = 1200
SLOW_SECONDS = 180

CMD_KINDS = [
    ("e2e", re.compile(r"playwright|test:e2e")),
    ("pytest", re.compile(r"\bpytest\b")),
    ("build", re.compile(r"npm run build|tsc -b|vite build|swift build|cargo build|go build")),
    ("lint", re.compile(r"npm run lint|eslint|ruff|swiftlint")),
    ("unit", re.compile(r"vitest|npm run test\b|npm test\b|jest\b|swift test|cargo test|go test|-m unittest")),
    ("ios", re.compile(r"xcodebuild")),
    ("android", re.compile(r"gradlew")),
]
CODEX_ERROR = re.compile(r'"exit_code":\s?[1-9]|Exit code: [1-9]|Process exited with code [1-9]|Script failed')
NOT_HUMAN = ("<task-notification", "<command-", "<system-reminder", "<local-command", "[Image")


def claude_globs():
    # A custom CLAUDE_CONFIG_DIR keeps transcripts there, but sessions started without it still use ~/.claude.
    roots = {os.path.expanduser("~/.claude"), os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")}
    return sorted(os.path.join(r, "projects", "*", "*.jsonl") for r in roots)


def codex_glob():
    root = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    return os.path.join(root, "sessions", "*", "*", "*", "*.jsonl")


def parse_ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def classify(cmd):
    return next((k for k, rx in CMD_KINDS if rx.search(cmd)), None)


@functools.lru_cache(maxsize=None)
def git_common_dir(path):
    try:
        out = subprocess.run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.stdout.strip() or None


def in_repo(cwd, repo_root, repo_git):
    if not cwd:
        return False
    if cwd == repo_root or cwd.startswith(repo_root + os.sep):
        return True
    # Worktrees outside the repository folder share its git dir while they still exist.
    return os.path.isdir(cwd) and git_common_dir(cwd) == repo_git


class Session:
    def __init__(self, agent, path, start, end):
        self.agent, self.path, self.start, self.end = agent, path, start, end
        self.title, self.cost, self.prs = "", 0.0, set()
        self.first = self.last = self.prev_when = None
        self.prev_text = ""
        self.stats = collections.Counter()
        self.kinds = collections.defaultdict(lambda: {"n": 0, "sec": 0.0})
        self.slow, self.errors, self.human, self.idle = [], collections.Counter(), [], []
        self.skills, self.spawned = collections.Counter(), collections.Counter()
        self.pending = {}

    def seen(self, when, conversational=True):
        if not (self.start <= when < self.end):
            return False
        self.first, self.last = self.first or when, when
        if conversational:
            if self.prev_when and (when - self.prev_when).total_seconds() > IDLE_SECONDS:
                self.idle.append({
                    "from": self.prev_when.astimezone().strftime("%H:%M"),
                    "to": when.astimezone().strftime("%H:%M"),
                    "minutes": round((when - self.prev_when).total_seconds() / 60),
                    "last_before": self.prev_text,
                })
            self.prev_when = when
        return True

    def said(self, text):
        if text.strip():
            self.prev_text = "agent said: " + text[-300:]

    def call(self, call_id, when, name, label):
        self.stats["tool_calls"] += 1
        self.pending[call_id] = (when, name, label)
        self.prev_text = f"waiting on tool {name}: {label[:120]}"

    def result(self, call_id, when, is_error, error_text=""):
        if call_id not in self.pending:
            return
        t0, name, label = self.pending.pop(call_id)
        sec = (when - t0).total_seconds()
        kind = classify(label)
        if kind:
            self.kinds[kind]["n"] += 1
            self.kinds[kind]["sec"] += sec
        if sec > SLOW_SECONDS:
            self.slow.append((round(sec), name, label[:120]))
        if is_error:
            self.errors[re.sub(r"\d+", "N", error_text[:120])] += 1

    def user_text(self, text):
        if not text.startswith(NOT_HUMAN):
            self.human.append(text[:200])

    def report(self):
        return {
            "agent": self.agent,
            "file": self.path,
            "title": self.title,
            "start": self.first.astimezone().strftime("%m-%d %H:%M"),
            "end": self.last.astimezone().strftime("%m-%d %H:%M"),
            "minutes": round((self.last - self.first).total_seconds() / 60),
            "cost_usd_session_total": round(self.cost, 2) if self.cost else None,
            "tokens": {k: self.stats[k] for k in ("in_tok", "out_tok", "cache_read_tok")},
            "tool_calls": self.stats["tool_calls"],
            "compactions": self.stats["compactions"],
            "aborted_turns": self.stats["aborted_turns"],
            "asked_user": self.stats["asked_user"],
            "cmd_kinds": {k: {"n": v["n"], "min": round(v["sec"] / 60, 1)} for k, v in self.kinds.items()},
            "slow_calls": sorted(self.slow, reverse=True)[:8],
            "repeated_errors": self.errors.most_common(6),
            "idle_gaps": self.idle,
            "last_event_in_window": self.prev_text,
            "human_messages": self.human[:10],
            "skills": dict(self.skills),
            "spawned_agents": dict(self.spawned),
            "prs": sorted(p for p in self.prs if p),
        }


def read_jsonl(path):
    with open(path) as f:
        for line in f:
            try:
                yield json.loads(line)
            except ValueError:
                continue


def claude_cwd(path):
    for d in read_jsonl(path):
        if d.get("cwd"):
            return d["cwd"]
    return None


def parse_claude(path, start, end):
    s = Session("claude", path, start, end)
    # One reply is written as several lines (thinking, text, tool use) that repeat the same message id and usage.
    usage_by_message = {}
    for line_number, d in enumerate(read_jsonl(path)):
        t = d.get("type")
        if t == "ai-title":
            s.title = d.get("aiTitle", "")
        elif t == "cost-state":
            s.cost = max(s.cost, d.get("totalCostUSD") or 0)
        elif t == "pr-link":
            s.prs.add(d.get("prNumber"))
        ts = d.get("timestamp")
        if not ts or not s.seen(parse_ts(ts), t in ("user", "assistant")):
            continue
        when = parse_ts(ts)
        if t == "system" and "compact" in str(d.get("subtype")):
            s.stats["compactions"] += 1
        msg = d.get("message") if isinstance(d.get("message"), dict) else {}
        content = msg.get("content")
        if t == "assistant":
            usage_by_message[msg.get("id") or line_number] = msg.get("usage") or {}
            for c in content or []:
                if c.get("type") == "text":
                    s.said(c.get("text", ""))
                if c.get("type") != "tool_use":
                    continue
                name, inp = c["name"], c.get("input") or {}
                label = inp.get("command", "") if name == "Bash" else name
                if name == "Skill":
                    s.skills[inp.get("skill")] += 1
                elif name == "Agent":
                    s.spawned[inp.get("subagent_type") or "general"] += 1
                elif name == "AskUserQuestion":
                    s.stats["asked_user"] += 1
                s.call(c["id"], when, name, label)
        elif t == "user":
            if isinstance(content, str):
                s.user_text(content)
                continue
            for c in content or []:
                if c.get("type") == "tool_result":
                    text = c.get("content")
                    text = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
                    s.result(c.get("tool_use_id"), when, bool(c.get("is_error")), text)
    for u in usage_by_message.values():
        s.stats["out_tok"] += u.get("output_tokens", 0)
        s.stats["in_tok"] += u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
        s.stats["cache_read_tok"] += u.get("cache_read_input_tokens", 0)
    return s


def codex_meta(path):
    for d in read_jsonl(path):
        if d.get("type") == "session_meta":
            p = d.get("payload") or {}
            src = p.get("source")
            spawn = src.get("subagent", {}).get("thread_spawn", {}) if isinstance(src, dict) else {}
            return p.get("cwd"), p.get("id"), spawn.get("parent_thread_id"), spawn.get("agent_path")
    return None, None, None, None


def codex_command(raw):
    m = re.search(r'\\?"cmd\\?"\s*:\s*\\?"(.*?)\\?"\s*[,}]', raw)
    return m.group(1) if m else raw[:160]


def parse_codex(path, start, end):
    s = Session("codex", path, start, end)
    for d in read_jsonl(path):
        ts = d.get("timestamp")
        t, p = d.get("type"), d.get("payload") or {}
        pt = p.get("type")
        if not ts:
            continue
        when = parse_ts(ts)
        conversational = t == "response_item" and pt in (
            "message", "custom_tool_call", "custom_tool_call_output", "function_call", "function_call_output")
        if not s.seen(when, conversational):
            continue
        if t == "token_usage_record":
            u = p.get("usage") or {}
            s.stats["out_tok"] += u.get("output_tokens", 0)
            s.stats["in_tok"] += u.get("input_tokens", 0) - u.get("cached_input_tokens", 0)
            s.stats["cache_read_tok"] += u.get("cached_input_tokens", 0)
        elif t == "compacted":
            s.stats["compactions"] += 1
        elif t == "event_msg" and pt == "turn_aborted":
            s.stats["aborted_turns"] += 1
        elif t == "event_msg" and pt == "item_completed":
            item = p.get("item") or {}
            if item.get("type") == "UserMessage":
                text = " ".join(c.get("text", "") for c in item.get("content") or [])
                s.title = s.title or text[:60]
                s.user_text(text)
        elif t == "event_msg" and pt == "task_complete":
            s.said(p.get("last_agent_message") or "")
        elif t == "response_item" and pt == "message" and p.get("role") == "assistant":
            s.said(" ".join(c.get("text", "") for c in p.get("content") or []))
        elif t == "response_item" and pt == "custom_tool_call":
            s.call(p.get("call_id"), when, p.get("name"), codex_command(p.get("input") or ""))
        elif t == "response_item" and pt == "function_call":
            name, args = p.get("name"), p.get("arguments") or ""
            if name == "spawn_agent":
                m = re.search(r'"task_name"\s*:\s*"([^"]+)"', args)
                s.spawned[m.group(1) if m else "agent"] += 1
            s.call(p.get("call_id"), when, name, codex_command(args) if name == "exec_command" else name)
        elif t == "response_item" and pt in ("custom_tool_call_output", "function_call_output"):
            out = p.get("output")
            text = out if isinstance(out, str) else "\n".join(c.get("text", "") for c in out or [] if isinstance(c, dict))
            s.result(p.get("call_id"), when, bool(CODEX_ERROR.search(text)), text.split("Output:", 1)[-1].strip())
    return s


def subagent_summary(rows):
    kinds = collections.defaultdict(lambda: {"n": 0, "min": 0.0})
    for r in rows:
        for k, v in r["cmd_kinds"].items():
            kinds[k]["n"] += v["n"]
            kinds[k]["min"] = round(kinds[k]["min"] + v["min"], 1)
    return {
        "count": len(rows),
        "out_tok": sum(r["tokens"]["out_tok"] for r in rows),
        "in_tok": sum(r["tokens"]["in_tok"] for r in rows),
        "cmd_kinds": kinds,
        "by_type": collections.Counter(r.get("subagent_type") for r in rows),
        "slow_calls": sorted((c + [r.get("subagent_type")] for r in rows for c in map(list, r["slow_calls"])), reverse=True)[:6],
        "repeated_errors": collections.Counter(e for r in rows for e, _ in r["repeated_errors"]).most_common(4),
    }


def collect(repo_root, start, end):
    repo_git = git_common_dir(repo_root)
    if not repo_git:
        raise ValueError(f"--repo {repo_root} is not a Git repository; pass the repository's main checkout")
    since = start.timestamp()
    sessions = []

    claude_files = {os.path.realpath(f) for g in claude_globs() for f in glob.glob(g)}
    for f in sorted(claude_files):
        if os.path.getmtime(f) < since or not in_repo(claude_cwd(f), repo_root, repo_git):
            continue
        main = parse_claude(f, start, end)
        subs = []
        for sf in glob.glob(os.path.join(f[:-6], "subagents", "*.jsonl")):
            sub = parse_claude(sf, start, end)
            if sub.first:
                row = sub.report()
                meta = sf[:-6] + ".meta.json"
                row["subagent_type"] = None
                if os.path.exists(meta):
                    with open(meta) as m:
                        row["subagent_type"] = json.load(m).get("agentType")
                subs.append(row)
        if not subs and (not main.first or not main.stats["tool_calls"]):
            continue
        if main.first:
            row = main.report()
        else:
            row = {"agent": "claude", "file": f, "title": f"(subagents of session {main.title or os.path.basename(f)} that started earlier)",
                   "start": min(r["start"] for r in subs), "end": max(r["end"] for r in subs)}
        row["subagents"] = subagent_summary(subs)
        sessions.append(row)

    codex_main, codex_subs = {}, collections.defaultdict(list)
    for f in glob.glob(codex_glob()):
        if os.path.getmtime(f) < since:
            continue
        cwd, sid, parent, agent_path = codex_meta(f)
        if not in_repo(cwd, repo_root, repo_git):
            continue
        s = parse_codex(f, start, end)
        if not s.first:
            continue
        if parent:
            row = s.report()
            row["subagent_type"] = (agent_path or "").rsplit("/", 1)[-1] or None
            codex_subs[parent].append(row)
        elif s.stats["tool_calls"]:
            codex_main[sid] = s.report()
    for sid, row in codex_main.items():
        row["subagents"] = subagent_summary(codex_subs.pop(sid, []))
        sessions.append(row)
    for parent, rows in codex_subs.items():
        # Parent session started before the window; keep its subagents' work visible.
        sessions.append({"agent": "codex", "title": f"(subagents of session {parent} that started earlier)",
                         "start": min(r["start"] for r in rows), "end": max(r["end"] for r in rows),
                         "subagents": subagent_summary(rows)})

    sessions.sort(key=lambda r: r["start"])
    return sessions


def parse_time(flag, text):
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{flag} {text!r} is not ISO 8601; use a value such as 2026-11-09 or 2026-11-09T07:00") from None
    # astimezone() on a naive value applies the system's DST rules for that instant.
    return when.astimezone()


def window(since, until, now):
    end = parse_time("--until", until) if until else now
    start = parse_time("--since", since) if since else end - timedelta(hours=24)
    if start >= end:
        raise ValueError(f"--since {start.isoformat()} is not before --until {end.isoformat()}")
    return start, end


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--since", help="start of the range; defaults to 24 hours before --until")
    ap.add_argument("--until", help="end of the range; defaults to now")
    args = ap.parse_args()
    repo_root = os.path.realpath(args.repo)
    try:
        start, end = window(args.since, args.until, datetime.now().astimezone())
        sessions = collect(repo_root, start, end)
    except ValueError as error:
        ap.error(str(error))
    out = {"repo": repo_root, "window": [start.isoformat(), end.isoformat()], "sessions": sessions}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1, default=list)


if __name__ == "__main__":
    main()
