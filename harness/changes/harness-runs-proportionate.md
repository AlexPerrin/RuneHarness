---
slug: harness-runs-proportionate
track: harness
title: "a PR's agent runs are proportionate to its change: genie #355 took 145 runs for two one-line fixes"
kind: change
priority: P0
mechanism: loop
deps: []
created: '2026-11-02T02:50:00Z'
---
The user (2026-11-01, ET): "Genie took many agent hours to accomplish, for two single line changes it was not worth it."

Evidence: state/runs: genie-review-355 134 runs, genie-355-bank-lamp 7, the three finding changes 4 (145 in all) for #355's two one-line fixes (requiredRights on ::randomevent; the bank lamp's eventsAllowed check removed). Causes seen today: whole-PR re-reviews on every seeded or changed contract row (fixed: verdict keyed to judged rows); qa runs stalled at an idle-logged-out login screen and re-run from scratch (harness-qa-login-idle); no-op dev and qa runs on answers that change no row (harness-answer-without-code-no-run); one qa run per maintainer finding re-judging the same head; ship/gate loops.

Acceptance: find every remaining cause in the run records (state/runs/genie-*.json, events.jsonl, transcripts) and fix each at its root, so a change's runs scale with its diff and findings: one dev and one qa run per real head move is the norm, and any further run names its cause in the run record's reason. A test pins the run count of a modeled PR with N findings and one head move. Report the run count per change before and after.

(harness-dep-on-fork-merge depends on this change only to order the two on the loop mechanism.)
