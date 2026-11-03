---
slug: harness-run-ends-with-change
track: harness
title: A live run whose change is done or closed ends and frees its slot
kind: change
priority: P0
deps: []
created: '2026-11-01T03:15:20Z'
---
harness-device-egress-ip-1 was resumed (events: "resumed ... 2026-11-01T02:32:58Z"), recorded its hand-over ("record": "handover", head bd388d7, 02:58:47 and again 02:59:02) and stopped at 02:59:13 with a plain-text reply, not SubagentHandback, so hook.end_run left it live (handed=False). The change went "done" at 03:04:39, yet `hd` still lists "run: harness-device-egress-ip-1 (dev, harness-device-egress-ip) since 2026-11-01T01:46:49Z" and state/runs/harness-device-egress-ip-1.json has ended null, record true. Nothing ends it: the pass ends only unstarted runs of a closed change (hd.py "a run listed before the close is never spawned") and runs whose console died. It holds one of the six agent slots: with cannon-review-354-7, client-devtools-login-1, client-host-runelite-fetches-1, harness-desktop-first-login-2 and harness-mobile-desktop-naming-1 live, busy (agents: 6) is true and client-login-index-log [client P0] "dev run due" is not spawned. Same shape earlier: quest-restlessghost-3 stayed ended null after its "ended" event (orchestrator-16). Fix: the pass ends a started run, with its record from produced(), once its change is done or closed, with an "ended" event (reason "change done"/"change closed"), so the slot frees on that fact. One test per requirement touched.
