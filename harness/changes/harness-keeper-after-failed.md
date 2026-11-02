---
slug: harness-keeper-after-failed
track: harness
title: after a keeper's FAILED login nothing logs the desktop in again
kind: change
priority: P1
mechanism: desktop
deps: []
created: '2026-11-02T06:18:23Z'
limit-of:
- server-clan-guest
---
sweep-46 P1-b: desktop_login.py keep() (fa658e pin ~164-180): r=FAILED while the client's gameState is LOGGED_IN; the retry loop exits, ready(since) is false, and the keeper waits for a LOGIN_SCREEN that never comes, leaving the desktop logged in with no inventory and no further keeper line; server-world-entities-11 has waited on it since 06:11:48Z. On FAILED the keeper logs out and retries (or ends and says so). Also (P2-a): the 10-tick check assumes the client's tick restarts at each login, but 7785 ran 0 -> 5 -> 97 across three logins; count from the first event after this login. evidence/monitor/sweep-46.md

Also (joined): The keeper's devtools polling cancels a run's calls, and a run's call ends the keeper
Monitor sweep 47 (evidence/monitor/sweep-47.md P0-a): the devtools plugin cancels the active tool on every tools/call (re/devtools/src/main/java/com/openrune/devtools/McpHttpServer.java:212-224, errorResult("Cancelled")), and the keeper polls get_client_state every 2 s (desktop_login.py keep(), wait(poll=2)). So any run call longer than ~2 s is cut off: world-entities-11 ~10 walk_to 'Cancelled' 06:19:35-06:21:08Z while get_client_state showed the player moving 3221->3131; clan-channels-5 type_chat/widget_action/interact_player from 05:58:47Z; cannon-8 wait_for/click/type_chat from 05:13:24Z. Reverse: a run's call cancels the keeper's login typing, call() raises Refused and keep() ends as if gone (state/server-world-entities/keep-7780.log 'keep: devtools endpoint on 7780 gone: type_chat: Cancelled', ~05:34Z), leaving the desktop unkept. Acceptance: a run's long calls (wait_for, walk_to) on a kept desktop are never Cancelled by the keeper; the keeper keeps the desktop logged in through a run's calls; Cancelled never reads as gone.

Also (joined): A keeper call queued behind a run's long call times out, ends the keeper and replays later
Monitor sweep 49 P1-a (evidence/monitor/sweep-49.md), on tools 6a1081baf: each owner call waits on DevtoolsOwner.ONE (DevtoolsOwner.java:63-82); the keeper's call() reads with urlopen(timeout=30) (desktop_login.py:64), and a read timeout raises a bare TimeoutError that neither call()'s retry nor whole() catches, so keep() falls to except OSError, prints 'keep: devtools endpoint on N gone' and exits (desktop_login.py:236-238). The abandoned request stays queued and runs later, replaying an ENTER or a half-typed name. A run's walk_to holds the endpoint up to 60 s+ (the bridge's wait_for timeoutMs 60000, mcp/devtools_bridge.py:173-175). Acceptance: a keeper call queued behind a run's call never ends the keeper, and a step it abandoned never runs later.

Also (server-clan-guest): up waits forever on a desktop whose devtools plugin could not bind its port
server-clan-guest-3 (2026-11-02 ~06:33Z): track.sh up server-clan-guest 2 claimed instance 11 (devtools port 7790); its client log (run/11/home/.runelite/logs/client.log) shows OpenRuneDevToolsPlugin 'Failed to start MCP server on port 7790' BindException: Address already in use (the port was free again a minute later, so likely a JVM of the instance's previous claim still closing). desktop_start (tools/track.sh:122-125) loops until the port is listened on or the launcher JVM exits; the client lives on without the endpoint, so up never ends. Acceptance: an up whose desktop's devtools endpoint cannot bind fails naming the bind error (or binds after the previous holder is gone), never waits without an ending fact.
