#!/usr/bin/env python3
"""hook.py: the one hook program, wired in .claude/settings.json (docs/ARCHITECTURE.md). Reads the event JSON on stdin.

SubagentStart   bind the listed run: the brief path in the agent's first message names it (else the oldest listed run of
                the role); record agent_id and the transcript path.                                                       R2
PreToolUse      bind if the start was missed; the one rule (R4): `hd approve` is denied inside a subagent.                 R4
PostToolUse     the context size (the transcript's last assistant usage) past cfg.context_limit → tell the run once to
                write evidence/<slug>/handoff.md and hand back.                                                            R6
SubagentStop    end the run: ended, usage, last message, record (the role's record newer than the start), then start the
                pass without waiting (`systemctl --user start --no-block hd-tick.service`, else a detached `hd tick`).     R2 R6
Never blocks an agent on the pass; never fails an agent: any error here is one event line.
"""
import json, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hd  # noqa: E402


def transcript(p):
    t = p.get("agent_transcript_path") or p.get("transcript_path")
    try:
        return [json.loads(l) for l in open(t) if l.strip()] if t else []
    except (OSError, ValueError):
        return []


def text_of(message):
    c = message.get("content")
    return c if isinstance(c, str) else " ".join(b.get("text", "") for b in (c or []) if isinstance(b, dict))


def brief_in(entries):
    """The run named by the one-line prompt `Read and follow state/briefs/<run>.md`."""
    for e in entries:
        if e.get("type") == "user":
            m = re.search(r"state/briefs/(\S+?)\.md", text_of(e.get("message", {})))
            return m.group(1) if m else None
    return None


ROLES = ("dev", "qa", "orchestrator")


def find_run(p, fallback=False):
    """By agent id (an index file: one read per call), else by the brief path in the transcript; a bind may fall back
    to the oldest listed run of the role."""
    aid = p.get("agent_id")
    idx = hd.STATE / "runs" / "by-agent" / str(aid)
    if aid and idx.exists():
        f = hd.STATE / "runs" / f"{idx.read_text()}.json"
        if f.exists():
            return json.loads(f.read_text())
    rs = hd.runs()
    name = brief_in(transcript(p))
    by_name = [r for r in rs if r["name"] == name and not r.get("ended")]
    listed = [r for r in rs if fallback and not r.get("started") and not r.get("ended") and r["role"] == p.get("agent_type")]
    return (by_name or listed or [None])[0]


def bind(p):
    if not p.get("agent_id") or p.get("agent_type") not in ROLES:
        return
    r = find_run(p, fallback=True)
    if not r or r.get("started"):
        return
    r.update(started=hd.now(), started_at=time.time(), agent_id=p["agent_id"], transcript=p.get("agent_transcript_path") or p.get("transcript_path"))
    hd.save_run(r)
    (hd.STATE / "runs" / "by-agent").mkdir(exist_ok=True)
    (hd.STATE / "runs" / "by-agent" / p["agent_id"]).write_text(r["name"])
    hd.event(change=r["change"], run=r["name"], action="started")


def usage_of(entries):
    u, last = {"turns": 0, "input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}, ""
    for e in entries:
        if e.get("type") != "assistant":
            continue
        m = e.get("message", {})
        if (us := m.get("usage")):
            u["turns"] += 1
            for k, f in (("input", "input_tokens"), ("output", "output_tokens"), ("cache_read", "cache_read_input_tokens"), ("cache_creation", "cache_creation_input_tokens")):
                u[k] += us.get(f) or 0
        last = text_of(m) or last
    return u, last[-500:]


def produced(r):
    """The run's record, newer than its start: a hand-over, verdict, question, agreed contract or filed change."""
    slug, since = r["change"], r.get("started") or r["listed"]
    if any(x and x["ts"] >= since for x in (hd.rec(slug, "handover"), hd.rec(slug, "ask"))):
        return True
    if any(v["ts"] >= since for v in hd.verdicts(slug)):
        return True
    con = hd.contract(slug)
    if con and con["agreed"] == r["name"]:
        return True
    f = hd.STATE / "events.jsonl"
    return f.exists() and any('"action": "new"' in l and json.loads(l)["ts"] >= since for l in open(f))


def start_pass():
    """The pass runs after every run end, never waited on."""
    r = subprocess.run(["systemctl", "--user", "start", "--no-block", "hd-tick.service"], capture_output=True)
    if r.returncode:
        hd.STATE.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([sys.executable, str(hd.ROOT / "hd.py"), "tick"], stdin=subprocess.DEVNULL, stdout=open(hd.STATE / "tick.log", "a"),
                         stderr=subprocess.STDOUT, start_new_session=True)


def end_run(p):
    r = find_run(p)
    if not r:
        return hd.event(action="stop-unmatched", agent=p.get("agent_id"), role=p.get("agent_type"))
    if r.get("ended"):
        return
    u, last = usage_of(transcript(p))
    r.update(ended=hd.now(), usage=u, last=(p.get("last_assistant_message") or last)[-500:], record=produced(r), events_at=hd.Facts().events_count())
    hd.save_run(r)
    hd.event(change=r["change"], run=r["name"], action="ended", record=r["record"], turns=u["turns"])
    start_pass()


def deny_approve(p):
    """R4: the one guard rule. Authority is otherwise by credential; the approval record is main's alone."""
    if p.get("agent_id") and re.search(r"\bhd(\.py)?\s+approve\b", (p.get("tool_input") or {}).get("command") or ""):
        hd.event(action="denied", agent=p["agent_id"], role=p.get("agent_type"), rule="hd approve is main's")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": "hd approve is recorded by main after the user's yes, never by an agent. Report it; do not work around it."}}))


def context_of(path):
    """The last assistant message's context size, from the transcript's tail (never the whole file)."""
    try:
        with open(path, "rb") as f:
            f.seek(max(0, f.seek(0, 2) - 65536))
            tail = f.read().split(b"\n")
    except (OSError, TypeError):
        return 0
    for line in reversed(tail):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") == "assistant" and (us := (e.get("message") or {}).get("usage")):
            return (us.get("input_tokens") or 0) + (us.get("cache_read_input_tokens") or 0) + (us.get("cache_creation_input_tokens") or 0)
    return 0


def context_limit(p):
    """R6: past cfg.context_limit the run is told once to write its hand-off and hand back; the successor is listed with it."""
    if p.get("agent_type") not in ROLES:
        return
    r = find_run(p)
    if not r or r.get("handoff_told"):
        return
    size = context_of(p.get("agent_transcript_path") or p.get("transcript_path"))
    if size < hd.cfg().get("context_limit", 150000):
        return
    r["handoff_told"] = size
    hd.save_run(r)
    hd.event(change=r["change"], run=r["name"], action="context-limit", tokens=size)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
          f"Context limit reached ({size} tokens): write evidence/{r['change']}/handoff.md (what is done, what is next, the facts you rely on), "
          "stop every process you started, and hand back now with `run " + r["name"] + ": handoff`. A fresh run continues from your file."}}))


def main():
    p = json.load(sys.stdin)
    try:
        {"SubagentStart": bind, "PreToolUse": lambda p: (bind(p), deny_approve(p)), "PostToolUse": context_limit, "SubagentStop": end_run}.get(p.get("hook_event_name"), lambda p: None)(p)
    except Exception as e:  # never fail an agent for a harness fault
        hd.event(action="hook-error", event=p.get("hook_event_name"), error=repr(e)[:300])


if __name__ == "__main__":
    main()
