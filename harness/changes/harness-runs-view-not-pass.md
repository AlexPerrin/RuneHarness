---
slug: harness-runs-view-not-pass
track: harness
title: dev and planner runs run full acting passes when they look at hd
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T04:13:17Z'
---
sweep-33 P1-a: bare 'python3 hd.py' is cmd_tick([]) with act=True (hd.py:3209); the role files call it hd (.claude/agents/dev.md:10, qa.md:9), so runs use it as a status view: 23 such calls since ~03:00Z (e.g. a270dea1e198c2706 03:58:03Z, afe9db38583c35d7b 03:57:58Z, a02ae8282278ea5dd 03:48:36Z, 03:51:58Z) list and stop runs, start gates and ships, and print the orchestrator's spawn lines into a dev's context; hook.py:8 denies only approve/close. A run gets a view (hd show / hd tick --dry-run) and the hook denies a bare hd or hd tick from a subagent. Also (sweep-33 P2-a): a started run keeps going after its change's step moves to another role (cannon -6 and goblin -9 qa alive at 04:12Z, their changes 'dev run due' since 03:56:21Z; hd.py:2397 handles only unstarted runs, hd.py:821 stops started ones only on a head move): tell or stop it the same way. evidence/monitor/sweep-33.md

Also (filed): hd verdict accepts a verdict from a run the pass already ended
sweep-34 P2-a: goblin-diplomacy-review-367-...-hzi4jq-1 was ended 'change superseded' ~03:55:58Z, then wrote a verdict at 03:56:19Z with run '' (hd.py:2901 finds no started unended qa); name-hash's 02:04:19Z verdict also has run ''. hd verdict refuses when no started, unended qa run of the change exists. evidence/monitor/sweep-34.md
