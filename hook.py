#!/usr/bin/env python3
"""hook.py: the one hook program, wired in .claude/settings.json (docs/ARCHITECTURE.md). Reads the event JSON on stdin.

SubagentStart   bind the listed run named by the brief path in the agent's own first message (never another run: agents
                spawned together start at once); record agent_id and the agent's transcript path. An agent whose brief
                names a run already ended is stopped at once (`continue: false`), its reason naming the run and why it
                ended, at the start or its first tool call; the run stays ended.                                          R2
PreToolUse      bind if the start found no prompt yet; `hd approve` and `hd close` are denied in a subagent or the orchestrator (the user types them as `!` commands, which fire no hook).  R4
                AskUserQuestion is denied in the orchestrator's session (its definition's frontmatter holds only name and description). R2
                A bare `hd` or `hd tick` (the acting pass) is denied in a subagent: a run views with `hd show` or `hd tick --dry-run`.  R5
                A run's kill of a pid outside its own slice, and its pkill or killall, is denied.                          R5
                A run's own agent whose run the pass, the head or `hd stop` ended stops at its next tool call (its hand-back goes). R2
                A git commit naming harness/ is denied while the definitions hold a dependency cycle.                      R5
                A run's Bash command, or one of an agent it spawned (its meta file's parentAgentId, at any depth), denied by
                none of these, starts with `hd scope <run>`: its shell joins the run's systemd slice, which the pass stops
                once the run ended (hd stop stops it at once).                                                           R5
                A run's SubagentHandback is denied while a background command, monitor or subagent it started has no task
                notification yet (a run cannot TaskStop its subagent: it asks it to return with SendMessage and waits).   R2
PostToolUse     the orchestrator's TaskStop of a run's agent (one resumed after its hand-back too) ends that run, as `hd stop` does.  R2
                a SendMessage to a live run's agent records when it was told: the contract rows written until then are its own.  R3
                the context size (the transcript's last assistant usage) past cfg.context_limit → tell the run once to
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
                never hands back ends by the orchestrator's TaskStop of its agent, `hd stop` or its console's death.                                      R2 R6
SessionStart    after a compaction of an orchestrator session acting on a reread definition, the live one is its context
                again (hd.reread): the compaction keeps only the one it started on.                                      R2
An agent a run spawned (its meta file names a parentAgentId: a reader, a fork) is part of that run: only the deny rules
and the run's slice apply to it, and it stops (continue: false) at its next tool call once that run has ended (the
slice's stop ends the command it waits on, so that call returns at once). A `reader`'s Bash command
that writes (a redirection to a file, rm/mv/cp, git that moves a ref, track.sh up/build/gate/down, docker run, a gh or
hd write) is denied.                                                                                         R5
Every write is a fact, a file of its own in state/facts/ (hd.fact), folded into the run records by the pass under its lock:
a hook never takes the lock, never waits on a pass. The deny rules run first and read only definitions and the command.
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


def parent_of(p):
    """The agent that spawned this one: Claude Code's agent-<id>.meta.json beside the agent's transcript names its
    parentAgentId when a subagent spawned it. Only the orchestrator spawns runs, so an agent with a parent is part of
    that parent's run (a reader, a fork), never a run itself."""
    t = agent_transcript(p)
    try:
        return json.loads(Path(t).with_suffix(".meta.json").read_text()).get("parentAgentId") if t else None
    except (OSError, ValueError, AttributeError):
        return None


def is_run(p):
    return p.get("agent_type") in ROLES and not parent_of(p)


def find_run(p):
    """By agent id (an index file: one read per call), else by the brief path in the agent's own transcript."""
    aid = p.get("agent_id")
    idx = hd.STATE / "runs" / "by-agent" / str(aid)
    if aid and idx.exists():
        if (r := hd.runs(idx.read_text())):
            return r[0]
    name = brief_in(transcript(p))
    return next((r for r in (hd.runs(name) if name else []) if not r.get("ended")), None)   # an ended run's agent is refused first


def refuse_ended(p):
    """R2: an agent whose brief names a run already ended (by the pass, the head, or another agent's hand-back) stops at
    once, the run left ended; a bound agent (its by-agent index) is its run's own and binds instead."""
    if not p.get("agent_id") or not is_run(p) or (hd.STATE / "runs" / "by-agent" / p["agent_id"]).exists():
        return
    name = brief_in(transcript(p))
    r = next(iter(hd.runs(name) if name else []), None)
    if not r or not r.get("ended") or r.get("agent_id") == p["agent_id"]:
        return
    why = r.get("reason") or "handed back"
    hd.event(change=r["change"], run=name, action="spawn-refused", agent=p["agent_id"], reason=why)
    msg = (f"run {name}: refused, it ended at {r['ended']} ({why}) before this agent started. Orchestrator: do not respawn it; "
           "spawn only what hd lists now.")
    ev = p.get("hook_event_name")
    if p.get("tool_name") == "SubagentHandback":   # its hand-back goes: the orchestrator reads the line
        return True
    out = {"continue": False, "stopReason": msg}
    if ev == "PreToolUse":
        out["hookSpecificOutput"] = {"hookEventName": ev, "permissionDecision": "deny", "permissionDecisionReason": msg + " Stop now: hand back this line."}
    elif ev == "SubagentStart":
        out["hookSpecificOutput"] = {"hookEventName": ev, "additionalContext": msg + " Run nothing: hand back this line."}
    print(json.dumps(out))
    return True


def bind(p):
    """R2: the binding is a fact file in state/facts/ (the pass folds it under its lock): never a wait on the pass."""
    if not p.get("agent_id") or not is_run(p):
        return
    r = find_run(p)
    if r and r.get("ended") and not r.get("reason") and r.get("agent_id") == p["agent_id"]:   # resumed after its hand-back
        hd.fact(fact="resumed", run=r["name"], agent_id=p["agent_id"])
        return hd.event(change=r["change"], run=r["name"], action="resumed")
    if not r or r.get("started"):   # nothing to write on each tool call
        return
    cpid, cstart = hd.Facts().console()
    hd.write(hd.STATE / "runs" / "by-agent" / p["agent_id"], r["name"])
    hd.fact(fact="bind", run=r["name"], agent_id=p["agent_id"], transcript=agent_transcript(p), console_pid=cpid, console_start=cstart, at=time.time())
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
    if p.get("tool_name") != "SubagentHandback" or not is_run(p) or not (ids := running(transcript(p))):
        return
    hd.event(action="handback-held", agent=p.get("agent_id"), tasks=ids)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason":
          f"Not yet: {', '.join(ids)} you started have not reported their end. A subagent: SendMessage it to return its answer "
          "now (you cannot TaskStop it), then block until its task notification; a background command or monitor: TaskStop it. "
          "Then hand back; each subagent's answer is kept in the change's evidence."}}))
    return True


def owner_run(p):
    """R5: the run whose processes an agent's are: its own, or, for an agent a run spawned (a reader, a fork, at any depth),
    the run of the nearest ancestor bound to one (parent_of, step by step)."""
    q, seen = p, set()
    while (aid := q.get("agent_id")) and aid not in seen:
        seen.add(aid)
        if (idx := hd.STATE / "runs" / "by-agent" / str(aid)).exists() and (r := hd.runs(idx.read_text())):
            return r[0]
        if not (parent := parent_of(q)):
            break
        q = {"agent_id": parent, "agent_transcript_path": str(Path(agent_transcript(q)).parent / f"agent-{parent}.jsonl")}
    return find_run(p) if is_run(p) else None   # a run's agent before its binding is folded


def in_run_slice(p):
    """R5: a run's Bash command, and each of the agents it spawned, starts with `hd scope <run>` on a line of its own: its
    shell moves into the run's slice, so every process it starts ends with the run (the permission rules still judge the
    command's own lines)."""
    if p.get("tool_name") != "Bash" or not (r := owner_run(p)):
        return
    ti = p.get("tool_input") or {}
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "updatedInput":
          {**ti, "command": f"python3 {Path(__file__).resolve().parent / 'hd.py'} scope {r['name']}\n{ti.get('command') or ''}"}}}))


def end_stopped(p):
    """R2: the orchestrator's TaskStop of a run's agent ends the run, as `hd stop` does (a killed agent fires no SubagentStop)."""
    aid = p.get("tool_name") == "TaskStop" and ((p.get("tool_input") or {}).get("task_id") or (p.get("tool_input") or {}).get("shell_id"))
    if not aid or not (f := hd.STATE / "runs" / "by-agent" / aid).exists():   # a background command or a non-run agent
        return
    hd.fact(fact="stopped", run=(name := f.read_text().strip()), agent_id=aid)
    hd.event(run=name, action="ended", reason="TaskStop")
    start_pass()


def told(p):
    """R3: a SendMessage to a run's agent tells it the contract as it stands: its rows written until then are its hand-over's, never late."""
    to = p.get("tool_name") == "SendMessage" and (p.get("tool_input") or {}).get("to")
    if to and (f := hd.STATE / "runs" / "by-agent" / str(to)).exists():
        name = f.read_text().strip()
        hd.fact(fact="told", run=name, **({"given": hd.given_now(r[0]["change"])} if (r := hd.runs(name)) else {}))


def start_pass():
    """The pass runs after every run end, never waited on."""
    r = subprocess.run(["systemctl", "--user", "start", "--no-block", "hd-tick.service"], capture_output=True)
    if r.returncode:
        hd.STATE.mkdir(parents=True, exist_ok=True)
        subprocess.Popen([sys.executable, str(hd.ROOT / "hd.py"), "tick"], stdin=subprocess.DEVNULL, stdout=open(hd.STATE / "tick.log", "a"),
                         stderr=subprocess.STDOUT, start_new_session=True)


def end_run(p):
    if not is_run(p):   # a nested agent's stop is its parent's notification, never a run's end
        return
    entries = transcript(p)
    r = find_run(p)
    if not r:
        return hd.event(action="stop-unmatched", agent=p.get("agent_id"), role=p.get("agent_type"))
    if r.get("reason"):   # ended by the pass or the head, not by a stop
        return
    u, last, handed = usage_of(entries)
    if not handed and (ids := running(entries)):   # R2: never idle on its own work
        hd.event(change=r["change"], run=r["name"], action="idle-refused", tasks=ids)
        return print(json.dumps({"decision": "block", "reason":
            f"Your background command(s) {', '.join(ids)} are still running. Never end a turn on your own work: block on it in the "
            "foreground with one until-loop on an observable fact (its output file, a log line, a port). A step that cannot "
            "finish (a hang, a refused login) is an error: stop it and hand back."}))
    rec = handed and bool(hd.produced(r) or r["role"] == "planner")  # the planner's hand-back is its record, filed or not
    if handed:   # an idle stop leaves the run live
        keep_answers(p, r, entries)
    hd.fact(fact="end", run=r["name"], usage=u, last=(last if handed else p.get("last_assistant_message") or last)[-500:], handed=handed, record=rec)
    if handed:
        hd.event(change=r["change"], run=r["name"], action="ended", record=rec, turns=u["turns"])
    start_pass()


def bare(p):
    """The Bash command with its data removed: heredoc bodies, and quoted arguments unless a -c or eval script."""
    raw = re.sub(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?=\n|$)", "", (p.get("tool_input") or {}).get("command") or "", flags=re.S)
    return re.sub(r"(?<!-c )(?<!eval )('[^']*'|\"[^\"]*\")", "''", raw)


def deny_ask(p):
    """R2: the orchestrator never waits on the user (it is the only spawner): AskUserQuestion is denied in its session, by a
    rule here rather than its definition's frontmatter, which a running session never rereads."""
    if p.get("tool_name") == "AskUserQuestion" and p.get("agent_type") == "orchestrator" and not p.get("agent_id"):
        hd.event(action="denied", role="orchestrator", rule="AskUserQuestion")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason":
              "You never wait on the user: ask as text in your reply (or `hd ask <slug>`) and go on with the loop."}}))
        return True


def deny_users_word(p):
    """R4: the one guard rule. Authority is otherwise by credential; the user's word (approve, close) is the user's own `!` command, which fires no hook."""
    cmd = bare(p)
    # only a command that runs hd: hd at the start of a command (after ; & | ( newline or $( ), never a mere mention
    # a subagent carries agent_id; the orchestrator, a top-level `claude --agent orchestrator` session, agent_type alone
    m = (p.get("agent_id") or p.get("agent_type")) and \
        re.search(r"(?:^|[;&|(\n])\s*(?:\w+=\S*\s+)*(?:python3?\s+)?(?:\S*/)?hd(\.py)?\s+(approve|close)\b", cmd)
    if m:
        hd.event(action="denied", agent=p.get("agent_id"), role=p.get("agent_type"), rule=f"hd {m[2]} is the user's")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"hd {m[2]} is the user's own word, typed by the user as a `!` command, never run by an agent. Report it; do not work around it."}}))
        return True


def deny_pass(p):
    """R5: a subagent views hd (`hd show`, `hd tick --dry-run`), never runs its acting pass: a bare `hd` or `hd tick` lists
    and ends runs, starts gates and ships, and prints the orchestrator's spawn lines. The orchestrator alone runs it."""
    if not p.get("agent_id") or not re.search(r"(?:^|[;&|(\n])\s*(?:\w+=\S*\s+)*(?:python3?\s+)?(?:\S*/)?hd(?:\.py)?(?:(?=[\s;&|)]|$)(?!\s+[A-Za-z])|\s+tick\b(?![^;&|\n]*--dry-run))", bare(p)):
        return
    hd.event(action="denied", agent=p.get("agent_id"), role=p.get("agent_type"), rule="hd pass in a subagent")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason":
          "a bare `hd` or `hd tick` is the orchestrator's acting pass: view with `hd show <slug>` or `hd tick --dry-run`."}}))
    return True


def deny_foreign_kill(p):
    """R5: a run signals only its own processes, those in its slice: a `kill` whose every target is a pid in the run's
    slice (or the shell's own job, %n) goes; a pkill or killall (a pattern matches other runs' processes) or a kill of
    any other pid is denied. A run's processes end with `track.sh down <slug>` or the run's own end."""
    if p.get("tool_name") != "Bash" or not (r := owner_run(p)):
        return
    sl, bad = hd.run_slice(r["name"]), []
    for m in re.finditer(AT + r"(pkill|killall|kill)\b([^;&|\n)]*)", bare(p)):
        args = [x for x in re.split(r"\s\d*[<>]", " " + m[2])[0].split() if not x.startswith("-")]   # shortcut: `kill -s SIG pid` reads SIG as a target and is denied; write `kill -SIG pid`
        if m[1] != "kill" or not args:
            bad.append(m[0].strip())
        for x in args if m[1] == "kill" else []:
            try:
                ok = x.startswith("%") or x.isdigit() and int(x) > 1 and f"/{sl}/" in Path(f"/proc/{x}/cgroup").read_text()
            except OSError:
                ok = False
            if not ok:
                bad.append(x)
    if not bad:
        return
    hd.event(change=r["change"], run=r["name"], action="denied", rule=f"kill outside the run's slice: {' '.join(bad)[:80]}")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason":
          f"a run signals only its own processes ({sl}); {' '.join(bad)[:120]!r} is a pattern or a pid outside it. Stop yours with "
          "`track.sh down <slug>`, or `kill <pid>` of a process you started (its pid from your own command's output)."}}))
    return True


AT = r"(?:^|[;&|(\n`]|\$\()\s*(?:\w+=\S*\s+)*(?:(?:sudo|env|nohup|exec|xargs(?:\s+-\S+)*)\s+)*"   # a command's position
WRITES = re.compile("|".join((
    r"(?<![-=>])\d*>>?\|?(?!&)\s*(?!/dev/null\b)[^\s&|;)]",                       # a redirection to a file
    AT + r"(?:rm|rmdir|mv|cp|tee|touch|mkdir|ln|chmod|chown|dd|truncate|install|kill|pkill|curl|wget)\b",
    AT + r"sed\s+(?:-\S+\s+)*-\w*i", r"-delete\b", r"-exec(?:dir)?\s+(?:rm|mv|cp)\b",
    AT + r"git(?:\s+-C\s+\S+)*\s+(?:commit|push|pull|fetch|checkout|switch|restore|reset|add|rm|mv|merge|rebase|"
         r"cherry-pick|revert|am|apply|stash|clean|tag|branch|worktree|update-ref|config|gc|prune)\b",
    r"\btrack\.sh\s+(?:up|build|gate|down|ship|measure|check-\S+)\b",
    AT + r"docker\s+(?!ps\b|logs\b|inspect\b|images\b)\w",
    AT + r"gh\s+(?!api\b)\w+\s+(?:create|edit|merge|close|reopen|comment|delete|review|ready|upload|run|rerun|cancel)\b",
    AT + r"gh\s+api\b[^;&|\n]*\s(?:-X\s*(?!\s|GET\b)|--method\s+(?!GET\b)|-f\b|-F\b|--field\b|--raw-field\b|--input\b)",
    AT + r"(?:python3?\s+)?(?:\S*/)?hd(?:\.py)?\s+(?!show\b)\w")))


def deny_reader_write(p):
    """R5: a `reader` reads only: a Bash command that writes a file, moves git, builds, brings up, runs a container or acts
    on GitHub or hd is denied (its rules say so; this makes it so)."""
    if p.get("agent_type") != "reader" or not (m := WRITES.search(bare(p))):
        return
    hd.event(action="denied", agent=p.get("agent_id"), role="reader", rule=f"reader writes: {m[0].strip()[:60]}")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason":
          f"a reader only reads ({m[0].strip()!r} writes or acts): read with cat, grep, sed -n, jq, git log/show/diff, gh api GET; "
          "if the answer needs a write, say so in your answer and let your run do it."}}))
    return True


def stop_ended(p):
    """R2 R5: an agent stops at its next tool call once its run has ended: a run's own agent when the pass, the head or
    `hd stop` ended it (its step moved or waits, its change went; the run's own hand-back ends it with no reason, and a resume
    reopens it), an agent the run spawned whatever ended it (the orchestrator's TaskStop of a run leaves its agents
    running, and a subagent can TaskStop none). So no agent acts for an ended run: no verdict, no hand-over."""
    own = p.get("agent_id") and (hd.STATE / "runs" / "by-agent" / str(p["agent_id"])).exists()
    if not (own or parent_of(p)) or not (r := owner_run(p)):
        return
    if not r.get("ended") or own and not r.get("reason") or p.get("tool_name") == "SubagentHandback":   # its last line may go
        return
    msg = f"{r['name']} ended ({r['reason']}): its agent stops." if own else f"{r['name']} ended: an agent it spawned stops with it."
    hd.event(change=r["change"], run=r["name"], action="agent-stopped" if own else "nested-stopped", agent=p.get("agent_id"))
    out = {"continue": False, "stopReason": msg}
    if p.get("hook_event_name") == "PreToolUse":
        out["hookSpecificOutput"] = {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": msg + " Stop now."}
    print(json.dumps(out))
    return True


def deny_dep_cycle(p):
    """R5: a definition commit (a git commit naming harness/) is denied while the definitions hold a dependency cycle."""
    cmd = (p.get("tool_input") or {}).get("command") or ""
    if re.search(r"\bgit\b[^;&|\n]*\bcommit\b", cmd) and "harness/" in cmd and (cy := hd.cycles(hd.defs("changes"))):
        why = "; ".join(" -> ".join(c) for c in cy)
        hd.event(action="denied", agent=p.get("agent_id"), role=p.get("agent_type"), rule=f"dependency cycle {why}")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"the definitions hold a dependency cycle ({why}): remove one of its deps, then commit."}}))
        return True


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
    if not is_run(p):
        return
    r = find_run(p)
    if not r or r.get("handoff_told"):
        return
    size = context_of(agent_transcript(p))
    if size < hd.cfg().get("context_limit", 150000):
        return
    hd.fact(fact="context-limit", run=r["name"], tokens=size)
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
    if not is_run(p) or not (r := find_run(p)) or r.get("ended"):
        return
    up, mine = hd.STATE / r["change"] / "up.json", hd.STATE / "runs" / "by-agent" / f"{p['agent_id']}.idle"
    try:
        mark, desktops = up.stat().st_mtime_ns, json.loads(up.read_text()).get("desktops")
    except (OSError, ValueError):
        return
    if not desktops:
        return
    try:   # the count is the agent's own (no run record written on each tool call)
        r = {**r, **json.loads(mine.read_text())}
    except (OSError, ValueError):
        pass
    if r.get("play_mark") != mark or (p.get("tool_name") or "").startswith("mcp__osrs-devtools-desktop__"):
        r.update(play_mark=mark, idle_calls=0, idle_told=False)
    else:
        r["idle_calls"] = r.get("idle_calls", 0) + 1
    tell = r["idle_calls"] >= IDLE_CALLS and not r["idle_told"]
    r["idle_told"] = r["idle_told"] or tell
    hd.write(mine, json.dumps({k: r[k] for k in ("play_mark", "idle_calls", "idle_told")}))
    if tell:
        hd.event(change=r["change"], run=r["name"], action="desktops-idle", desktops=desktops)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
              f"Your desktops ({desktops}) have had no devtools call in your last {IDLE_CALLS} tool calls. A desktop is up only "
              f"while you play in it: run your track script's `down {r['change']}` now, and `RESUME=1 ... up {r['change']} [N]` "
              "(the accounts as down saved them) when you next act in game."}}))


def reread(p):
    """R2: a compacted orchestrator session holds again the live definition it last read."""
    if t := hd.reread(hd.Facts(), force=True):
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext":
              f"Your definition is the live {hd.ORCH}, which replaces the one you started on:\n{t}"}}))


def main():
    p = json.load(sys.stdin)
    try:
        {"SessionStart": reread, "SubagentStart": lambda p: refuse_ended(p) or bind(p), "PreToolUse": lambda p: stop_ended(p) or refuse_ended(p) or (deny_ask(p) or deny_users_word(p) or deny_pass(p) or deny_foreign_kill(p) or deny_dep_cycle(p) or deny_reader_write(p) or hold_handback(p) or in_run_slice(p), bind(p)), "PostToolUse": lambda p: told(p) or end_stopped(p) or stop_ended(p) or context_limit(p) or idle_desktops(p), "SubagentStop": end_run}.get(p.get("hook_event_name"), lambda p: None)(p)
    except Exception as e:  # never fail an agent for a harness fault
        hd.event(action="hook-error", event=p.get("hook_event_name"), error=repr(e)[:300])


if __name__ == "__main__":
    main()
