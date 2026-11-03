"""Claude Code hooks (docs/ARCHITECTURE.md §12, §13): bind the orchestrator session and each run, end a run on its
one-line hand-back, deny the user's two commands to agents, put each run's shell in its scope, tell a run or the
session when its context passes the limit. stdin: the hook's JSON; stdout: the answer. Wired in .claude/settings.json."""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import act  # noqa: E402
import store  # noqa: E402
from store import ROOT, event, now  # noqa: E402

BRIEF = re.compile(r"state/briefs/(\d+)\.md")
DENY = re.compile(r"\bhd(\.py)?\s+(approve|close)\b")
HD = f"python3 {ROOT}/harness/hd.py"


def claude_pid():
    """The nearest ancestor that is the claude process: (pid, start) or None."""
    pid = os.getppid()
    while pid > 1:
        try:
            argv0 = open(f"/proc/{pid}/cmdline", "rb").read().split(b"\0")[0].decode()
            if os.path.basename(argv0) == "claude":
                return pid
            pid = int(open(f"/proc/{pid}/status").read().split("PPid:")[1].split()[0])
        except (OSError, IndexError, ValueError):
            return None
    return None


def context_tokens(path) -> int:
    """The context size from the transcript's last usage record (input + cache read + cache creation)."""
    try:
        with open(path, "rb") as f:
            f.seek(max(0, os.path.getsize(path) - 262144))
            for line in reversed(f.read().decode(errors="replace").splitlines()):
                if '"usage"' not in line:
                    continue
                u = json.loads(line).get("message", {}).get("usage")
                if u:
                    return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    except (OSError, ValueError):
        pass
    return 0


def run_of(db, agent_id):
    return db.execute("SELECT * FROM run WHERE agent_id=? AND ended_at IS NULL", (agent_id,)).fetchone()


def session_start(e):
    """A top-level session binds: a session row with the claude pid, its role (the orchestrator by agent type; any other
    session in this checkout is the driver, the user's chat) and the definition it loaded."""
    pid = claude_pid()
    if pid:
        db = store.connect()
        role = "orchestrator" if e.get("agent_type") == "orchestrator" else "driver"
        db.execute("INSERT OR IGNORE INTO session(pid, pid_start, session_id, definition, started_at, role) VALUES (?,?,?,?,?,?)",
                   (pid, int(open(f"/proc/{pid}/stat").read().rsplit(")", 1)[1].split()[19]), e["session_id"], act.definition_blob(), now(), role))
    return {}


def session_end(e):
    db = store.connect()
    db.execute("UPDATE session SET ended_at=?, end_kind='exit' WHERE session_id=? AND ended_at IS NULL", (now(), e["session_id"]))
    return {}


def bind(db, agent, run_id):
    """An agent that names its brief (or its record line) is the run's agent; the run starts then."""
    if db.execute("UPDATE run SET agent_id=?, started_at=? WHERE id=? AND agent_id IS NULL AND ended_at IS NULL",
                  (agent, now(), run_id)).rowcount:
        r = run_of(db, agent)
        event(db, "started", r["change"], r["id"], f"{r['role']} agent {agent}")
        return r
    return None


def tool_text(e) -> str:
    ti, name = e.get("tool_input", {}), e.get("tool_name")
    return ti.get("command", "") if name == "Bash" else ti.get("message", "") if name == "SubagentHandback" else ti.get("file_path", "")


def end(db, r, line, m, tpath=""):
    """The run ends on its record line: end_kind handback (or handoff), its scope stopped, a pass started."""
    db.execute("UPDATE run SET ended_at=?, end_kind=?, record=?, usage_json=?, transcript=? WHERE id=?",
               (now(), "handoff" if m.group(2) == "handoff" else "handback", line,
                json.dumps({"context_tokens": context_tokens(tpath)}), tpath, r["id"]))
    event(db, "ended", r["change"], r["id"], line)
    act.stop_scope(r["id"])
    act.tick_later()


def pre_tool_use(e):
    """`hd approve` / `hd close` are the user's own → deny. In a run: bind on the first read of its brief; every
    Bash command runs after `hd scope <run>` so its processes sit in the run's scope."""
    ti, name, text = e.get("tool_input", {}), e.get("tool_name"), tool_text(e)
    if name == "Bash" and DENY.search(text):
        db = store.connect()
        r = run_of(db, e.get("agent_id")) if e.get("agent_id") else None
        event(db, "denied", r["change"] if r else None, r["id"] if r else None, text[:200])
        store.alert(db, "denied", f"{r['id'] if r else 'orchestrator'}:approve-close", text[:200])
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": "hd approve and hd close are the user's own commands (typed with !)"}}
    agent = e.get("agent_id")
    if not agent:
        return {}
    db = store.connect()
    r = run_of(db, agent)
    if not r:
        gone = db.execute("SELECT * FROM run WHERE agent_id=? AND end_kind IN ('close','stop') ORDER BY id DESC LIMIT 1", (agent,)).fetchone()
        if gone:   # the run ended under the agent: nothing it does counts
            why = "its change was closed by the user" if gone["end_kind"] == "close" else "the orchestrator stopped it"
            return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                           "permissionDecisionReason": f"run {gone['id']} ended: {why}. Stop now, with no hand-back and nothing else."}}
        m = BRIEF.search(text)
        r = bind(db, agent, int(m.group(1))) if m else None
        if not r:
            return {}
    if name == "SubagentHandback":   # the hand-back as a tool call: its message is the line
        line = text.strip().splitlines()[-1].strip() if text.strip() else ""
        m = store.RECORD.match(line)
        if m and int(m.group(1)) == r["id"]:
            end(db, r, line, m, os.path.join(os.path.dirname(e["transcript_path"]), e["session_id"], "subagents", f"agent-{agent}.jsonl"))
            return {}
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                       "permissionDecisionReason": f"Hand back exactly one line and nothing beside it: run {r['id']}: <record>, as the brief's last section says."}}
    if name == "Bash":
        return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                       "updatedInput": {**ti, "command": f"{HD} scope {r['id']}; {ti['command']}"}}}
    return {}


def post_tool_use(e):
    """Context past hd.yaml context_limit: a run is told once to hand off; the orchestrator session drains."""
    import yaml
    limit = yaml.safe_load(open(os.path.join(ROOT, "hd.yaml")))["context_limit"]
    agent = e.get("agent_id")
    path = e["transcript_path"]
    if agent:
        path = os.path.join(os.path.dirname(path), e["session_id"], "subagents", f"agent-{agent}.jsonl")
        db = store.connect()
        m = BRIEF.search(tool_text(e))
        if m and not run_of(db, agent):
            bind(db, agent, int(m.group(1)))
    tokens = context_tokens(path)
    if tokens < limit:
        return {}
    db = store.connect()
    if not agent:
        if db.execute("UPDATE session SET drain_at=?, drain_why='context limit' WHERE session_id=? AND ended_at IS NULL AND drain_at IS NULL",
                      (now(), e["session_id"])).rowcount:
            event(db, "drain", None, None, f"context at {tokens} tokens: spawn nothing, hd restart once no run is live")
        return {}
    r = run_of(db, agent)
    if not r or db.execute("SELECT 1 FROM event WHERE kind='context' AND run=?", (r["id"],)).fetchone():
        return {}
    event(db, "context", r["change"], r["id"], f"{tokens} tokens")
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
            f"Your context is at {tokens} tokens, past the limit of {limit}. Hand off now: commit your work on your dev branch, "
            f"stop the processes you started, write evidence/{r['change']}/handoff.md (what is done, what is left, where things are), "
            f"then hand back exactly: run {r['id']}: handoff"}}


def subagent_stop(e):
    """The last line is the run's record → end the run (its scope stopped, a pass started). No record: a run with a
    background task pending is waiting for it (its notification resumes the agent), left alone; an idle one is asked
    once for the line, and a second idle stop ends the run without a record."""
    db = store.connect()
    msg = (e.get("last_assistant_message") or "").strip()
    line = msg.splitlines()[-1].strip() if msg else ""
    m = store.RECORD.match(line)
    r = run_of(db, e.get("agent_id")) or (m and bind(db, e.get("agent_id"), int(m.group(1))))
    if not r:
        return {}
    if m and int(m.group(1)) == r["id"]:
        end(db, r, line, m, e.get("agent_transcript_path", ""))
        return {}
    elif e.get("background_tasks"):
        return {}
    elif not e.get("stop_hook_active"):
        return {"decision": "block", "reason": f"Hand back exactly one line and nothing beside it: run {r['id']}: <record>, as the brief's last section says."}
    else:
        db.execute("UPDATE run SET ended_at=?, end_kind='console' WHERE id=?", (now(), r["id"]))
        event(db, "ended", r["change"], r["id"], f"no hand-back line: {line[:120]}")
    act.stop_scope(r["id"])
    act.tick_later()
    return {}


HANDLERS = {"SessionStart": session_start, "SessionEnd": session_end, "PreToolUse": pre_tool_use,
            "PostToolUse": post_tool_use, "SubagentStop": subagent_stop}


def main() -> None:
    e = json.load(sys.stdin)
    handler = HANDLERS.get(e.get("hook_event_name", ""))
    print(json.dumps(handler(e) if handler else {}))


if __name__ == "__main__":
    main()
