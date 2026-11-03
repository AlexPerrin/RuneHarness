---
slug: harness-taskstop-ends-scoped-bash
track: harness
title: TaskStop of a Bash that hd scope moved into a run scope leaves the shell running
kind: change
priority: P1
mechanism: runs
deps: []
created: '2026-11-02T05:18:04Z'
---
sweep-41 P1-a': server-clan-channels-4 TaskStopped 7 background tasks (beqso35os ... bmx3hezeb); Claude Code marked them killed, but the shells, moved by 'hd scope' into hd-server_clan_channels_4-<pid>.scope, kept running until the run pkill'd them at 05:15:08Z. A TaskStop of a scoped Bash stops its scope. evidence/monitor/sweep-41.md

Also (filed): a run ended for a wait loses its hand-off, and a met dependency re-gating ends dev work
server-clan-guest-2 (dev) was ended mid-work when hd marked its change 'waiting on server-clan-channels' (a dependency that had been met and was re-gating); the hook then refused every tool call, so the run could not write evidence/server-clan-guest/handoff.md (the orchestrator wrote evidence/server-clan-guest/handoff-run2.md from its report) and its first build died exit 144. server-clan-channels-4 and server-examine-multi-transform-2 were ended the same way at 05:20:31Z. An ended run may still write its evidence and hand back; and a dependency that was met and only re-gates (tools ship, new head of the dep) does not end a dependent's started run — only a wait that blocks the run's work (an open question, an unmet dependency) does.

Also (filed): a run's record is what that run handed back; a run the pass ended never settles its step
planner-27: three changes stuck at 05:21:26Z with 'handed back its record, yet its step is still due on the same input: no run is listed' (server-examine-multi-transform-2 dev, server-clan-guest-2 dev, server-clan-channels-4 qa). None of them handed back: the pass ended each at 05:20:31Z with reason 'waiting on <dep>' (events.jsonl 8932, and the clan pair just above it) when its met dependency re-gated on a new tools key (server-npc-examine-without-overlay 'gate on d4523cd5f-21ec60df2-9686679aa'), and stored record=True from produced(r). produced() (hd.py ~2278) counts any 'action: new' event in the run's window as its record, whoever filed it: harness-taskstop-ends-scoped-bash, filed by the orchestrator at 05:18:04Z, fell inside all three windows (state/runs/server-examine-multi-transform-2.json: last null, usage null, record true). unlistable() (hd.py ~2025) then reads that stored record as a settling hand-back, so the step, due again on the same input once the dep re-gated, never lists a run. Root cause against R5: a record is the run's own hand-back, but produced() reads a global event and unlistable() trusts a record the pass assigned. Fix: a filing counts only for the run that filed it (the new event names its filer's change or run), and unlistable settles a step only on a run that ended by its own hand-back (no pass-set reason); a run the pass ended neither settles the step nor counts toward the one-retry limit. This replaces the produced() any-filing rule. Acceptance: a test where another change is filed during a run that the pass then ends gives that run no record and lists the next run on the same input; the three changes above get their runs with no state edited by hand.
