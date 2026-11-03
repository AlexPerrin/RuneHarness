---
slug: harness-devtools-endpoint-owner
track: harness
title: 'any process can drive any desktop: the devtools endpoint answers whoever calls
  it'
kind: change
priority: P1
mechanism: devtools
deps: []
limit-of:
- hunter-feat-pr
- server-world-entities
created: '2026-11-02T05:43:53Z'
---
sweep-43 P0-a: the stray input on desktop1:7780 ('/hi::item egg 1', chat tick 592, 04:57:26Z) came from quest-cooksassistant-14's own script evidence/quest-cooksassistant/qa14/qdt.py, whose P = int(os.environ.get('PORT', '7780')) had no PORT set while its up was desktop2:7781; npc-examine-6 owned 7780. The same helper sits in qa15, interrupt/, server-445/play/ and quest-witchspotion/. The hook's port rule covers only mcp__osrs-devtools-* calls; every endpoint is open on 127.0.0.1 to any process. An instance's endpoint answers only its owner: a per-up token in state/<slug>/up.json the endpoint requires (the bridge and run scripts pass it). Correct harness-up-owns-its-instance's body: its hygiene stays, its diagnosis was wrong. evidence/monitor/sweep-43.md

Also (filed): A desktop devtools call went unanswered for over 5 minutes
Monitor sweep 47 P1-a: clan-channels-5 called hover {port 7780} at 06:24:20Z and had no tool_result at 06:29:46Z (tool_use/tool_result paired in its transcript), though mcp/devtools_bridge.py:39,72-83 bounds every desktop call to ANSWER_WAIT 30 s + timeoutMs; desktop1 was alive (log 06:25:44Z). Cause unconfirmed (a stuck bridge thread or reply, or the hook/a prompt on the Claude Code side). Acceptance: every desktop call returns within its bound, observed against a hung or preempted endpoint.

Also (filed): The devtools token refuses every run of a session whose bridge predates serve.py
harness-devtools-endpoint-owner-2's hand-back: the orchestrator session (pid 2233291, started 19:12 EST) and session 207579 run mcp/devtools_bridge.py directly at 20b99e3, not through serve.py, so they never load a shipped bridge and send no token. Every run the orchestrator spawns uses its bridges, so once this change ships every desktop brought up after it refuses all of those runs' devtools calls (401) until the orchestrator restarts. Acceptance: shipping the token never leaves a live run's desktop calls refused, e.g. the endpoint takes calls without a token until no session predating serve.py is live (read from the processes, not a time), or the ship waits on that fact.

Also (hunter-feat-pr): Server tools test kills every 'sleep 30' on the host
Root cause: tools/server/test_tools.py test_one_up_restart_or_down_of_a_slug_at_a_time ends with `pkill -f '^sleep 30$'`, which stops every `sleep 30` on the host, not only the one its fake track.sh started. The server gate's gate_ci loop waits with `sleep 30` between reads of the CI runs, so a harness ship gate running the server tools suite (ship-harness at 3c233c6, 2026-11-02T06:34:17Z to 06:36:43Z) SIGTERMed hunter-feat-pr's gate-ci at 06:36:13Z: row ci 'Terminated' rc 143 while CI run 41400863187 at the same sha was still running green. Any other sleep 30 on the host (keepers, other gates, waits) is hit the same way. PROBLEM/PRD: a process is stopped only by whoever started it. Fix: the test stops only the process it started (its own pid or process group, e.g. record the background sleep's pid in the test dir and kill that, or run it under a unique argv), and a check that no tools test calls pkill/killall on a pattern it does not own.

Also (filed): Nothing ends a run whose devtools call never returns
Monitor sweep 48 P1-a: server-clan-channels-5 last wrote its transcript at 06:24:20Z (hover on 7780) and was still hung at 06:45:41Z with its record live and 5 keepers polling; the orchestrator's stale bridge (pid 2233412, pre-0989166) has only a 240 s per-read urlopen timeout and no whole-call bound. The orchestrator stopped the run. Acceptance: a run's desktop call always returns within its bound in every live session (stale bridges included, or no run is spawned on one).

Also (server-world-entities): Server tools test kills every 'sleep 30' on the host
server-world-entities-12: the gate of server-world-entities at T 8d0e20c4a (gate commit 88c122034) failed row ci with 'Terminated' rc 143 at 2026-11-02T06:48:42Z, 93 s after gate-ci started (06:47:09Z): its 'sleep 30' between reads of the CI runs was SIGTERMed, the same kill as hunter-feat-pr's (tools/server/test_tools.py test_one_up_restart_or_down_of_a_slug_at_a_time ends with pkill -f '^sleep 30$'). A gate fails on a process another run stopped. Fix as stated on this mechanism: the test stops only the process it started.

Also (filed): A stale session's desktop bridge 401s its runs, and legacy() keeps the owner guard off while it lives
Monitor sweep 50 P0-a: the orchestrator's desktop bridge (pid 2233412, started 00:11Z, before d925d51) sends no token and never reloads: world-entities-11 got 401 on list_objects (7787, 7788) at 06:43:13Z and wrote evidence/server-world-entities/dt.py around it; clan-channels-6 got 401 on get_var (7782) at 06:54:55Z; aa6b02e52's legacy() spares only ups started after it, and while 2233412 or 207818 (session 207579) live, every up starts unguarded, so the guard never turns on. Acceptance: no live run's desktop call is refused for want of a token, and the owner guard is on for every up once no pre-serve.py bridge lives; legacy() goes once it has no use.
