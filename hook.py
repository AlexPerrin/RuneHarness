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


def find_run(p):
    rs, aid = hd.runs(), p.get("agent_id")
    by_id = [r for r in rs if aid and r.get("agent_id") == aid]
    if by_id:
        return by_id[0]
    name = brief_in(transcript(p))
    by_name = [r for r in rs if r["name"] == name and not r.get("ended")]
    listed = [r for r in rs if not r.get("started") and not r.get("ended") and r["role"] == p.get("agent_type")]
    return (by_name or listed or [None])[0]


def bind(p):
    if not p.get("agent_id"):
        return
    r = find_run(p)
    if not r or r.get("started"):
        return
    r.update(started=hd.now(), started_at=time.time(), agent_id=p["agent_id"], transcript=p.get("agent_transcript_path") or p.get("transcript_path"))
    hd.save_run(r)
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
    """The pass runs after every run end, never waited on (v7 waited on it inside the hook and was cancelled)."""
    r = subprocess.run(["systemctl", "--user", "start", "--no-block", "hd-tick.service"], capture_output=True)
    if r.returncode:
        hd.STATE.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([sys.executable, str(hd.ROOT / "hd.py"), "tick"], stdin=subprocess.DEVNULL, stdout=open(hd.STATE / "tick.log", "a"),
                         stderr=subprocess.STDOUT, start_new_session=True)


def end_run(p):
    r = find_run(p)
    if not r or r.get("ended"):
        return
    u, last = usage_of(transcript(p))
    r.update(ended=hd.now(), usage=u, last=(p.get("last_assistant_message") or last)[-500:], record=produced(r), events_at=hd.Facts().events_count())
    hd.save_run(r)
    hd.event(change=r["change"], run=r["name"], action="ended", record=r["record"], turns=u["turns"])
    start_pass()


def deny_approve(p): ...     # R4


def context_limit(p): ...    # R6


def main():
    p = json.load(sys.stdin)
    try:
        {"SubagentStart": bind, "PreToolUse": lambda p: (bind(p), deny_approve(p)), "PostToolUse": context_limit, "SubagentStop": end_run}.get(p.get("hook_event_name"), lambda p: None)(p)
    except Exception as e:  # never fail an agent for a harness fault
        hd.event(action="hook-error", event=p.get("hook_event_name"), error=repr(e)[:300])


if __name__ == "__main__":
    main()
