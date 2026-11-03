---
slug: harness-no-join-into-depended
track: harness
title: A change that others wait on takes no joined filing until it ships
kind: change
priority: P1
mechanism: contract
deps: []
created: '2026-11-02T21:31:23Z'
---
Sweep 87 P2-a: harness-filestore-track-1 filed its flaky-test limit as harness-attempts-test-mtime-flake (state/events.jsonl:11549, 21:22:37), filestore became its dependent (11550); 3 minutes later the orchestrator's sweep-86 filing (deps_held rewrite) was routed by mechanism loop into that same change (11560), so filestore (handed over cb682c3 21:26:09) waits on a one-test flake fix shipping with a rewrite it never needed. merge_limit (hd.py:3627-3640) joins any filing to the open change of its mechanism without checking for dependents (limit-of / deps). P4-a, same root: harness-attempts-test-mtime-flake (loop) and harness-tree-transitive-central-2 (tree) now both edit deps_held (hd.py:1622-1644) in parallel worktrees: the mechanism is the filer's label, not ownership of the code. A change with waiting dependents takes no join (the filing opens its own change or waits behind it). Evidence: evidence/monitor/sweep-87.md

Also (filed): A joined filing holds the changes it names until its dep hands over after the join
Sweep 88 P1-a: client-login-segv-osclient-5's limit joined harness-live-stack-issuer as answer-5 and added the dep client-login-segv-osclient -> harness-live-stack-issuer (state/events.jsonl:10851-10852). 2c15195 (bafff20) removed 'joined and ctx.done(dep, dh)' from deps_held, so client-login-segv-osclient-6 was listed and started at 21:34:23/36 (11598-11600) while harness-live-stack-issuer has not acted on answer-5 (still 'waiting on server-token-refusal-logged', 11378): the run debugs a login the issuer cannot land yet. A filing joined with --blocks (or naming its finder in limit-of) holds those changes until the dep hands over after the join; every other dependent goes on. The new R2 test covers only an unrelated join. P2-a: late_answers classified the user's answer by the text prefix 'the user:' while d4f21fe writes 'the user, to "Q": ...' (hd.py:3420): misclassified 21:24:36-21:34:23 until 2c15195; classify by a field, not a prefix, and test nxt's late-answer path with a quoting row. Evidence: evidence/monitor/sweep-88.md
