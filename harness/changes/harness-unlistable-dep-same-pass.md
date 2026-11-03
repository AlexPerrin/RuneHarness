---
slug: harness-unlistable-dep-same-pass
track: harness
title: unlistable clears a filed dependency by the test deps_held uses
kind: change
priority: P1
deps: []
created: '2026-11-01T19:54:05Z'
---
unlistable() (hd.py ~line 1066) clears a run that filed a dependency only when the dep is in shut_changes(): closed, or a recorded state from an earlier pass that starts with done. deps_held() (line 711) lets the dependent go due as soon as ctx.live(dep, head) holds. The two tests disagree for one pass: the dep is live (shipped) but its recorded state is still "shipping". In that pass the step is due, the run filed a dep, the dep is not yet in shut, so a false alert fires and a planner run is listed.
Evidence (state/events.jsonl):
- 19:43:17Z dep client-down-stops-mobile-login -> harness-mobile-allow-ports, filed inside run client-down-stops-mobile-login-2 (started 19:28:29Z, ended 19:43:32Z, record true, input ["", "e130103fe1ca", 0])
- 19:52:17Z harness-mobile-allow-ports state "shipping"
- 19:52:18Z client-down-stops-mobile-login state "dev run due"
- 19:52:19Z planner-14 listed on "client-down-stops-mobile-login: dev run client-down-stops-mobile-login-2 handed back its record, yet its step is still due on the same input: no run is listed"
- the next hd pass shows harness-mobile-allow-ports done and lists client-down-stops-mobile-login-3: the alert was false and planner-14 was spent on it.
This happens every time a dev-filed dependency ships, unless the dep is closed in that same pass.
Fix: one test for "the dep no longer holds". The step is only due when deps_held() returned None, so a dep the last run filed is already cleared. Drop shut_changes() from unlistable, and treat any dep event inside the run window as leaving the step listable. Proof: a test with a dep that is live but recorded "shipping" gives no alert from unlistable and a listed dev run.
