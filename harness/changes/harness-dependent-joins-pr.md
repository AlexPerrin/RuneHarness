---
slug: harness-dependent-joins-pr
track: harness
title: A change that depends on another open upstream PR joins that PR; nothing waits
  on an upstream merge
kind: change
priority: P0
deps: []
created: '2026-11-01T18:39:15Z'
---
The user's choice (2026-11-01), asked about test_a_dependency_on_another_pr_waits_for_its_upstream_merge ('this is a blocking operation, is it necessary?'): "Fold into one PR". harness-card-from-own-gate (19af661) makes a same-track dependent of another open upstream PR wait for that PR's upstream merge before any dev, QA or deploy, which parks the server-clan chain (server-clan-channels, -guest, -broadcasts, -hall behind server-friends-chat-clan-channels), server-examine-multi-transform, quest-dorics and quest-impcatcher. Acceptance: a change whose same-track dependency goes upstream as an open PR (or will: a new PR not yet opened) ships in that same PR: same public branch, its commits on top of the dependency's head, one card and one ship for the PR's new head; the PR's texts cover both changes; the 'waiting on X's upstream merge' state and its R2 test are removed; the no-stacking rule stays (a PR holds only its own changes' commits); tests cover a dependent joining its dependency's open PR and a dependent of a not-yet-opened PR shipping in the same new PR.

The user's word on genie-review-355 (2026-11-01): "It's not ready then." A PR's card (and its ready step) is offered only when every open change on the same PR (its maintainers' findings: e.g. genie-355-bank-lamp for #355's line-213 finding) is in the head; a card with a finding still outside the head is never offered. A test covers a PR with one finding change not yet joined: no card.
