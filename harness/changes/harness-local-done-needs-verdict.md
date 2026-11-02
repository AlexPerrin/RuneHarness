---
slug: harness-local-done-needs-verdict
track: harness
title: a local change whose head reached the live tree went done over a failed verdict
kind: change
priority: P1
mechanism: loop
deps: []
created: '2026-11-02T03:41:24Z'
---
server-world-entities (kind: local) had qa verdict FAIL 3 rows at 488270104 (server-world-entities-8: a5-range, accuracy, style); dev run -9 was fixing it when, at the 03:33:10Z live deploy, the pass marked the change 'done' (03:33:50Z, run ended 'change done') and then stopped the run's slice on every long command (exit 144). A local change is done only when its head is live AND its last verdict passes; a failed head is not in the live integration tree. evidence: state/events.jsonl 03:30:10-03:40:44Z; server-world-entities-9's hand-back.

Also (filed): the held-dependency alert stays after the dependent's card is held too
harness-dep-on-fork-merge's alert ('server-token-auth's card waits on central-token-login-op's upstream merge, whose card the user holds ...: lift it or hold this card too') still shows after the orchestrator held server-token-auth's card with the user's words (hd hold server-token-auth, ~03:5xZ, 'We will bundle the upstream auth contribution in the future'). Holding the dependent's card is one of the two ways out it names, so it must clear the alert.

Also (filed): the held-dependency alert is the user's choice, yet it lists a planner run
planner-25 was listed on public()'s alert (hd.py:1676) 'server-token-auth's card waits on central-token-login-op's upstream merge, whose card the user holds: ... lift it (hd hold central-token-login-op --lift) or hold this card too'. Both ways out are the user's word (hd hold is R4's user no/word); the planner can do neither, and the orchestrator had already held server-token-auth with the user's words. Root cause against PRD (the user decides on cards; runs never stand in for the user's word): the alert addresses the user but is not marked as the user's, so plan() (hd.py:2070, which skips 'user:' alerts) lists a planner on it. Fix: the alert is a 'user:' alert, like Docker down and no orchestrator; with the filing already joined here (it clears once the dependent's card is held), no planner is ever listed on it. Acceptance (test): a dependent waiting on a held cross-repo dep shows a 'user:' alert and plan() lists no planner run; once the dependent is held the alert is gone. Evidence: state/briefs/planner-25.md; hd output 03:5xZ.
