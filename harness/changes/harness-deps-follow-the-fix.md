---
slug: harness-deps-follow-the-fix
track: harness
title: A dependency follows its fix when hd new supersedes or joins it
kind: change
priority: P0
mechanism: contract
deps: []
created: '2026-11-02T00:55:05Z'
---
Planner-19 (monitor). A dependency names a fix by slug, and hd new moves the fix without moving the dependency, so a change stops waiting while its fix is still open. (1) --supersedes: server-cache-clientscript-name-hash has deps [gate-ci-external-fetch-failure, harness-github-reads-budget]; planner-17 superseded gate-ci-external-fetch-failure into harness-build-gate-keyed-process, shut() (hd.py:1786) counts a superseded change as done, so the dep reads satisfied and the change was gated and is 'gate failed: dev' again at 00:52:37Z on 'CI cancelled/completed', the very failure the open fix removes. (2) --blocks on a join: hd new harness-gate-infra-fail-no-dev --mechanism build-gate --blocks goblin-367-rsprox-dump (planner-19) printed 'merged into harness-build-gate-keyed-process' and goblin-367-rsprox-dump's deps stayed [goblin-diplomacy-review-367-fftgsrq]: merge_limit (hd.py:2685) ignores o.blocks, so the blocked change never waits, gets dev runs with nothing to fix (goblin-367-rsprox-dump-4, -5 re-handed over ea08bce28) and a planner run (planner-19). Root cause against PRD: a change waits on the fix it needs; the fix's identity is the change that carries it, and hd new rewrites that identity (supersede, join) without the waiting change following. Acceptance (each with a test): when hd new supersedes a change or joins a filing into an open change, every dependency on the superseded change and the --blocks target is rewritten to the change that now carries the fix (cycle-checked as now); a test supersedes a dep and asserts the dependent shows 'waiting on <superseder>'; a test joins with --blocks and asserts the blocked change's deps gain the joined-into change. The run also rewrites the live definitions this left behind: server-cache-clientscript-name-hash's dep gate-ci-external-fetch-failure becomes harness-build-gate-keyed-process, and goblin-367-rsprox-dump gains harness-build-gate-keyed-process.

Also (filed): a seeded check row invalidates every verdict: a verdict is keyed to the whole contract hash
sweep-14 B3: hd.py:1355 counts a verdict only if v['contract'] == con['hash']. The spotless check row seeded into ~25 contracts at 23:56:24Z made genie-review-355, hunter-feat-pr, server-friends-chat-clan-channels, server-clan-channels, genie-355-bank-lamp and the quests 'review due' at unchanged heads. A check row is gated, never judged: key a verdict to the judged rows only, as rule rows already are by their shas. evidence/monitor/sweep-14.md
