---
slug: h-route-failures-brief-reruns
track: harness
priority: P2
---
# a failure goes to the step that can fix it; a re-run starts from its predecessor's findings

The user (2026-11-09, after the v9 KPI review): file both fixes as one change. Two v9 KPIs miss their targets because dev runs start with nothing to change or start cold.

## 1. A failure goes to the step that can fix it
decide.dev_due (decide.py:261) starts a dev for every failure since the submission: build, gate, ship, CI, a FAIL verdict, a staging conflict. In the window 2026-11-03..09, 23 of 197 submissions (12%; 11 on 11-09) were a dev resubmitting the head it was started on, because the failure was not in the head:
- outside the head (9): gate CI 401 Bad credentials and `remote:` (runs 156, 162, 395), Formatting checked on the wrong tree (398), `BUILD FAILED in 7s` and fork-tools flakes (64, 65, 133, 308, 332), a ship merge with the live tip (245);
- only a waiver or a question clears it (4): verdict FAIL on rows whose remedy is another change (404, 405 on bb9b886; 139; 349);
- replay gate wanting evidence/<slug>/replay.md only (6: 206, 227, 230, 265, 273, 389).
Done when: a failure outside the head re-gates the same head once (a second failure raises an alert, no dev); a FAIL whose rows only a waiver or question can clear opens the question with no dev run; only a failure in the head starts a dev. `hd kpi` reports "dev runs that resubmitted the same head" (target 0); the existing successor-runs row stays.

## 2. A re-run starts from what its predecessor learned
act.brief_text (act.py:217) carries the predecessor's notes only when it ended on a context hand-off (handoff.md). A re-run starts cold: dev re-runs take a median 21.5 tool calls before the first edit against 23.5 for a first run (fork 23, client 22; target <=10), ~15 of them grep/find/cat. Client definitions that name a file reach the first edit in 12 calls against 22.5.
Done when: a dev brief lists the files the change's dev branch touches against its base (git diff --stat) and the previous run's hand-back line with what failed after it; `hd kpi` reports the median tool calls before the first edit for dev runs.
