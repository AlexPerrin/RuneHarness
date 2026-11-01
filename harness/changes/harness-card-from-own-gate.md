---
slug: harness-card-from-own-gate
track: harness
title: A change's card comes from its own gate on its head merged with upstream main;
  the shared test-server deploy is separate; PRs are self-contained, never stacked
kind: change
priority: P0
deps: []
created: '2026-11-01T18:20:25Z'
---
The user's word (2026-11-01): "offer a card once the change's own gate passes, on its head merged with upstream main, and treat the shared test-server deploy as separate. Ensure PRs are contained and not stacked". Today a card waits until the change is live on the shared test server (T_int = upstream main + permanent pins + every gated head), so one pin's conflict (content/looting-bag vs content/pirates-treasure, content/genie, feat/hunter in ObjTakePlugin.kt) blocks the cards of unrelated self-contained PRs: goblin-diplomacy-review-367-fftgsrq, server-friends-chat-clan-channels, quest-cooksassistant. Acceptance: (1) a change's card is offered once its own gate has passed on T = its head merged onto current upstream main alone (no pins, no other changes), with its contract's verdict at that head; (2) deploying to the shared test server is a separate step that never holds a card or a ship; a T_int conflict goes to the conflict's owner as now, but blocks only the test-server deploy; (3) every upstream PR is self-contained: its branch is based on upstream main, contains only its own commits, and no PR's branch contains another open PR's commits; the gate fails a head that reaches another change's unmerged commits (stacking) and the card names the base; (4) a dependency between changes whose PRs both go upstream is either merged upstream first (the dependent waits for 'merged', not 'live') or the two are one PR; (5) tests cover: a card offered while T_int conflicts; a stacked head refused at the gate; a dependent change waiting on its dependency's upstream merge.
