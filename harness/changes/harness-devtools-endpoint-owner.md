---
slug: harness-devtools-endpoint-owner
track: harness
title: 'any process can drive any desktop: the devtools endpoint answers whoever calls
  it'
kind: change
priority: P1
mechanism: devtools
deps: []
created: '2026-11-02T05:43:53Z'
---
sweep-43 P0-a: the stray input on desktop1:7780 ('/hi::item egg 1', chat tick 592, 04:57:26Z) came from quest-cooksassistant-14's own script evidence/quest-cooksassistant/qa14/qdt.py, whose P = int(os.environ.get('PORT', '7780')) had no PORT set while its up was desktop2:7781; npc-examine-6 owned 7780. The same helper sits in qa15, interrupt/, server-445/play/ and quest-witchspotion/. The hook's port rule covers only mcp__osrs-devtools-* calls; every endpoint is open on 127.0.0.1 to any process. An instance's endpoint answers only its owner: a per-up token in state/<slug>/up.json the endpoint requires (the bridge and run scripts pass it). Correct harness-up-owns-its-instance's body: its hygiene stays, its diagnosis was wrong. evidence/monitor/sweep-43.md

Also (filed): A desktop devtools call went unanswered for over 5 minutes
Monitor sweep 47 P1-a: clan-channels-5 called hover {port 7780} at 06:24:20Z and had no tool_result at 06:29:46Z (tool_use/tool_result paired in its transcript), though mcp/devtools_bridge.py:39,72-83 bounds every desktop call to ANSWER_WAIT 30 s + timeoutMs; desktop1 was alive (log 06:25:44Z). Cause unconfirmed (a stuck bridge thread or reply, or the hook/a prompt on the Claude Code side). Acceptance: every desktop call returns within its bound, observed against a hung or preempted endpoint.

Also (filed): The devtools token refuses every run of a session whose bridge predates serve.py
harness-devtools-endpoint-owner-2's hand-back: the orchestrator session (pid 2233291, started 19:12 EST) and session 207579 run mcp/devtools_bridge.py directly at 20b99e3, not through serve.py, so they never load a shipped bridge and send no token. Every run the orchestrator spawns uses its bridges, so once this change ships every desktop brought up after it refuses all of those runs' devtools calls (401) until the orchestrator restarts. Acceptance: shipping the token never leaves a live run's desktop calls refused, e.g. the endpoint takes calls without a token until no session predating serve.py is live (read from the processes, not a time), or the ship waits on that fact.
