#!/usr/bin/env python3
"""hook.py: the one hook program, wired in .claude/settings.json (docs/ARCHITECTURE.md). Reads the event JSON on stdin.

SubagentStart   bind the listed run named by the brief path in the agent's own first message (never another run: agents
                spawned together start at once); record agent_id and the agent's transcript path.                         R2
PreToolUse      bind if the start found no prompt yet; `hd approve` and `hd close` are denied in a subagent or the orchestrator (the user types them as `!` commands, which fire no hook).  R4
                A git commit naming harness/ is denied while the definitions hold a dependency cycle.                      R5
                A run's SubagentHandback is denied while a background command, monitor or subagent it started has no task
                notification yet (a run cannot TaskStop its subagent: it asks it to return with SendMessage and waits).   R2
PostToolUse     the context size (the transcript's last assistant usage) past cfg.context_limit → tell the run once to
                start no new work and hand off cleanly: commit (and, off the harness track, push) its work in progress on the
                dev ref, record what it judged, collect its subagents and stop its processes, write evidence/<slug>/handoff.md, hand back; else, while the
                change's up.json lists desktops, IDLE_CALLS tool calls in a row with no desktop devtools call since that up
                → tell the run once to `down` until it next plays (a devtools call or a new up starts the count again).   R6
SubagentStop    record usage and last message; the stop after SubagentHandback also ends the run with its record (the
                role's record newer than the start and the change's last answer; each subagent's hand-back is kept as
                evidence/<slug>/subagent-<id>.md). Any other stop leaves the run live,
                and is refused while a background command the agent started has not reported its end: the agent
                blocks on its own work, never idles on it (R2). Then start the pass without
                waiting (`systemctl --user start --no-block hd-tick.service`, else a detached `hd tick`). A run that
                never hands back ends by `hd stop` (TaskStop) or its console's death.                                      R2 R6
Never blocks an agent on the pass; never fails an agent: any error here is one event line.
"""
import json, re, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hd  # noqa: E402


def agent_transcript(p):
    """The agent's own transcript: SubagentStart and PreToolUse carry only the session's transcript_path, beside which
    the agent's lives at <session>/subagents/agent-<agent_id>.jsonl."""
    if p.get("agent_transcript_path"):
        return p["agent_transcript_path"]
    t = p.get("transcript_path")
    if t and p.get("agent_id"):
        return str(Path(t).with_suffix("") / "subagents" / f"agent-{p['agent_id']}.jsonl")
    return t


def transcript(p):
    t = agent_transcript(p)
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


ROLES = ("dev", "qa", "planner")


def find_run(p):
    """By agent id (an index file: one read per call), else by the brief path in the agent's own transcript."""
    aid = p.get("agent_id")
    idx = hd.STATE / "runs" / "by-agent" / str(aid)
    if aid and idx.exists():
        f = hd.STATE / "runs" / f"{idx.read_text()}.json"
        if f.exists():
            return json.loads(f.read_text())
    name = brief_in(transcript(p))
    return next((r for r in hd.runs() if name and r["name"] == name and not r.get("ended")), None)


def bind(p):
    if not p.get("agent_id") or p.get("agent_type") not in ROLES:
        return
    r = find_run(p)
    if not r or r.get("started") and (not r.get("ended") or r.get("reason")):  # nothing to write: no lock on each tool call
        return
    with hd.lock():  # R5: a pass reads and saves runs under the same lock: decide on the run read under it
        bind_locked(p)


def bind_locked(p):
    r = find_run(p)
    if r and r.get("ended") and not r.get("reason") and r.get("agent_id") == p["agent_id"]:   # resumed after its hand-back
        r["ended"] = None
        hd.save_run(r)
        return hd.event(change=r["change"], run=r["name"], action="resumed")
    if not r or r.get("started"):
        return
    cpid, cstart = hd.Facts().console()
    r.update(started=hd.now(), started_at=time.time(), agent_id=p["agent_id"], transcript=agent_transcript(p),
             console_pid=cpid, console_start=cstart)
    hd.save_run(r)
    (hd.STATE / "runs" / "by-agent").mkdir(exist_ok=True)
    (hd.STATE / "runs" / "by-agent" / p["agent_id"]).write_text(r["name"])
    hd.event(change=r["change"], run=r["name"], action="started")


def usage_of(entries):
    u, last, handed = {"turns": 0, "input": 0, "output": 0, "cache_read": 0, "cache_creation": 0}, "", False
    for e in entries:
        if e.get("type") != "assistant":
            continue
        m = e.get("message", {})
        if (us := m.get("usage")):
            u["turns"] += 1
            for k, f in (("input", "input_tokens"), ("output", "output_tokens"), ("cache_read", "cache_read_input_tokens"), ("cache_creation", "cache_creation_input_tokens")):
                u[k] += us.get(f) or 0
        last = text_of(m) or last
        for b in m.get("content") or []:  # the hand-back's report is the run's last word
            if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "SubagentHandback":
                last, handed = str((b.get("input") or {}).get("message") or ""), True
            elif isinstance(b, dict) and b.get("type") == "tool_use":   # resumed after a hand-back: work goes on
                handed = False
    return u, last, handed


def running(entries):
    """Background commands, monitors and subagents the agent started (a result's backgroundTaskId, taskId or async
    agentId) with no task notification yet; one TaskStop stopped (its result's task_id) or no longer finds counts as ended."""
    started, done = set(), set()
    for e in entries:
        t = e.get("toolUseResult")
        if isinstance(t, dict) and (tid := t.get("backgroundTaskId") or t.get("taskId") or (t.get("isAsync") and t.get("agentId"))):
            started.add(tid)
        if isinstance(t, dict) and t.get("task_id"):
            done.add(t["task_id"])
        done.update(a or b for a, b in re.findall(r"<task-id>(\w+)</task-id>|No task found with ID: (\w+)", json.dumps(e)))
    return sorted(started - done)


def subagents(entries):
    """The async subagents the agent started, by id."""
    return [t["agentId"] for e in entries if isinstance(t := e.get("toolUseResult"), dict) and t.get("isAsync") and t.get("agentId")]


def keep_answers(p, r, entries):
    """Each subagent's hand-back, read from its transcript beside the run's, kept in the run's evidence."""
    for aid in subagents(entries):
        _, answer, handed = usage_of(transcript({"agent_transcript_path": str(Path(agent_transcript(p)).parent / f"agent-{aid}.jsonl")}))
        if handed and answer:
            (hd.EVID / r["change"]).mkdir(parents=True, exist_ok=True)
            (hd.EVID / r["change"] / f"subagent-{aid}.md").write_text(answer + "\n")


def hold_handback(p):
    """R2: a run hands back only once every background task and subagent it started has reported its end."""
    if p.get("tool_name") != "SubagentHandback" or p.get("agent_type") not in ROLES or not (ids := running(transcript(p))):
        return
    hd.event(action="handback-held", agent=p.get("agent_id"), tasks=ids)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason":
          f"Not yet: {', '.join(ids)} you started have not reported their end. A subagent: SendMessage it to return its answer "
          "now (you cannot TaskStop it), then block until its task notification; a background command or monitor: TaskStop it. "
          "Then hand back; each subagent's answer is kept in the change's evidence."}}))


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
    if r.get("reason"):   # ended by the pass or the head, not by a stop
        return
    entries = transcript(p)
    u, last, handed = usage_of(entries)
    if not handed and (ids := running(entries)):   # R2: never idle on its own work
        hd.event(change=r["change"], run=r["name"], action="idle-refused", tasks=ids)
        return print(json.dumps({"decision": "block", "reason":
            f"Your background command(s) {', '.join(ids)} are still running. Never end a turn on your own work: block on it in the "
            "foreground with one until-loop on an observable fact (its output file, a log line, a port). A step that cannot "
            "finish (a hang, a refused login) is an error: stop it and hand back."}))
    r.update(usage=u, last=(last if handed else p.get("last_assistant_message") or last)[-500:])
    if handed:   # an idle stop leaves the run live
        rec = hd.produced(r) or r["role"] == "planner"  # the planner's hand-back is its record, filed or not
        r.update(ended=hd.now(), record=rec)
        keep_answers(p, r, entries)
    hd.save_run(r)
    if handed:
        hd.event(change=r["change"], run=r["name"], action="ended", record=r["record"], turns=u["turns"])
    start_pass()


def deny_users_word(p):
    """R4: the one guard rule. Authority is otherwise by credential; the user's word (approve, close) is the user's own `!` command, which fires no hook."""
    raw = re.sub(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", "", (p.get("tool_input") or {}).get("command") or "", flags=re.S)  # heredoc bodies are data
    cmd = re.sub(r"(?<!-c )(?<!eval )('[^']*'|\"[^\"]*\")", "''", raw)  # a quoted argument is data, unless it is a -c or eval script
    # only a command that runs hd: hd at the start of a command (after ; & | ( newline or $( ), never a mere mention
    # a subagent carries agent_id; the orchestrator, a top-level `claude --agent orchestrator` session, agent_type alone
    m = (p.get("agent_id") or p.get("agent_type")) and \
        re.search(r"(?:^|[;&|(\n])\s*(?:\w+=\S*\s+)*(?:python3?\s+)?(?:\S*/)?hd(\.py)?\s+(approve|close)\b", cmd)
    if m:
        hd.event(action="denied", agent=p.get("agent_id"), role=p.get("agent_type"), rule=f"hd {m[2]} is the user's")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"hd {m[2]} is the user's own word, typed by the user as a `!` command, never run by an agent. Report it; do not work around it."}}))


def deny_dep_cycle(p):
    """R5: a definition commit (a git commit naming harness/) is denied while the definitions hold a dependency cycle."""
    cmd = (p.get("tool_input") or {}).get("command") or ""
    if re.search(r"\bgit\b[^;&|\n]*\bcommit\b", cmd) and "harness/" in cmd and (cy := hd.cycles(hd.defs("changes"))):
        why = "; ".join(" -> ".join(c) for c in cy)
        hd.event(action="denied", agent=p.get("agent_id"), role=p.get("agent_type"), rule=f"dependency cycle {why}")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"the definitions hold a dependency cycle ({why}): remove one of its deps, then commit."}}))


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
    size = context_of(agent_transcript(p))
    if size < hd.cfg().get("context_limit", 150000):
        return
    r["handoff_told"] = size
    hd.save_run(r)
    hd.event(change=r["change"], run=r["name"], action="context-limit", tokens=size)
    ch = hd.defs("changes").get(r["change"]) or {}
    dev = hd.TRACK.get(ch.get("track"), {}).get("dev", "").format(slug=r["change"])
    save = ("" if not dev or r["role"] != "dev" else "commit your work in progress, built or not, " +
            (f"on {dev} in your clone (a local ref, never pushed); " if ch.get("track") == "harness"
             else f"in your clone and push it to {dev.replace('/', ' ', 1)}; "))   # fork/dev/<slug> → `fork dev/<slug>`
    judged = ("" if r["role"] != "qa" else "record what you judged: `hd verdict` with the failing rows and every unchecked "
              "row not-judged if a row failed, else each judged row with its result in handoff.md; ")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
          f"Context limit reached ({size} tokens): start no new work (no new step, lookup or subagent); finish only the "
          f"command in hand, then hand off cleanly, in this order: {save}{judged}"
          "collect every subagent you started (SendMessage it to return its answer now, then block until its task "
          "notification; TaskStop cannot stop it) and stop every process you started (TaskStop, your track script's `down "
          f"{r['change']}`); write evidence/{r['change']}/handoff.md (your commit, what is proven and by "
          "which evidence, what is left, the exact next step, whether a server or desktop is still up, the facts you rely on); "
          "then hand back with `run " + r["name"] + ": handoff`. A fresh run, listed in the same pass, resumes from your commit and file."}}))
    return True


IDLE_CALLS = 10   # tool calls with desktops up and none played in them: the run is building, reading or writing


def idle_desktops(p):
    """R6: a run keeps desktops up only while it plays in them; a stretch of other tool calls is told once."""
    if p.get("agent_type") not in ROLES or not (r := find_run(p)) or r.get("ended"):
        return
    up = hd.STATE / r["change"] / "up.json"
    try:
        mark, desktops = up.stat().st_mtime_ns, json.loads(up.read_text()).get("desktops")
    except (OSError, ValueError):
        return
    if not desktops:
        return
    if r.get("play_mark") != mark or (p.get("tool_name") or "").startswith("mcp__osrs-devtools-desktop__"):
        r.update(play_mark=mark, idle_calls=0, idle_told=False)
    else:
        r["idle_calls"] = r.get("idle_calls", 0) + 1
    tell = r["idle_calls"] >= IDLE_CALLS and not r["idle_told"]
    r["idle_told"] = r["idle_told"] or tell
    hd.save_run(r)
    if tell:
        hd.event(change=r["change"], run=r["name"], action="desktops-idle", desktops=desktops)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
              f"Your desktops ({desktops}) have had no devtools call in your last {IDLE_CALLS} tool calls. A desktop is up only "
              f"while you play in it: run your track script's `down {r['change']}` now, and `RESUME=1 ... up {r['change']} [N]` "
              "(the accounts as down saved them) when you next act in game."}}))


def main():
    p = json.load(sys.stdin)
    try:
        {"SubagentStart": bind, "PreToolUse": lambda p: (bind(p), deny_users_word(p), deny_dep_cycle(p), hold_handback(p)),"PostToolUse": lambda p: context_limit(p) or idle_desktops(p), "SubagentStop": end_run}.get(p.get("hook_event_name"), lambda p: None)(p)
    except Exception as e:  # never fail an agent for a harness fault
        hd.event(action="hook-error", event=p.get("hook_event_name"), error=repr(e)[:300])


if __name__ == "__main__":
    main()
