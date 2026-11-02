---
slug: harness-limit-of-holds-the-change
track: harness
title: a --limit-of filing joined into an open change does not hold the change it
  limits
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T03:08:28Z'
---
goblin-367-rsprox-dump-7, cannon-354-...gelgiq-5, server-friends-chat-clan-channels-21 each filed the openrs2 freshCache fault with hd new --limit-of <self>; it joined harness-deploy-survives-tools-ship, but none of the three gained it as a dependency, so each was 'gate failed: dev' again at the same head and goblin-367-rsprox-dump-8 was listed for nothing (03:1xZ). A limit-of filing, new or joined, adds the change it carries to the limited change's deps (as --blocks does). The orchestrator added the dep by hand to goblin, cannon, friends-chat, genie-review-355 and server-token-auth.

Also (filed): a dependency reopened by a joined filing still counts as met: its dependents run with nothing to fix
planner-24 (alert: server-cache-clientscript-name-hash: dev run server-cache-clientscript-name-hash-6 handed back its record, yet its step is still due on the same input). server-cache-clientscript-name-hash deps include harness-carry-gh-pr-edit-classic-projects (3cde033), whose fix for its limit (an upstream CI step the head reads dying on an openrs2 fetch) joined after its done head: hd shows it 'dev run due: a filing joined after the done head (answer-5, answer-6, answer-7)'. deps_held (hd.py:1390-1411) judges a cross-track dependency by ctx.live(dep, head): its last head is on v8, so the dependency is met and name-hash stays 'FAIL upstream at 8c6d9679e: dev'; run -6 (input ['carry', 8c6d9679e, 03:03:14Z]) found nothing to fix, re-handed over 8c6d9679e (events 03:08:26Z), and the step stayed due on the same input. Root cause against PRD (a change waits on the fix it needs until that fix is live): a dependency is judged by its head, not by its change's step; a joined filing or late answer reopens the change (hd.py:1446) but not the wait. Acceptance (with a test): a dependency is met only when its change's own step is done (or closed), so a reopened dependency holds its dependents with 'waiting on <dep>', for every track and the same-track upstream case alike; with harness-limit-of-holds-the-change's dep edge, a limited change never gets a run before the fix carrying its limit is live.
