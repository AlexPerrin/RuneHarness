---
slug: harness-handover-honours-reopen
track: harness
title: hd handover refuses a head whose failed CI the user's reopen answers
kind: change
priority: P1
mechanism: carry
limit-of:
- server-cache-clientscript-name-hash
deps: []
created: '2026-11-02T15:29:18Z'
---
server-cache-clientscript-name-hash (#448) head 8c6d9679e, definition reopen: 8c6d9679ee5bc7ce6f4f7b6c7ecc8c458f2b4958 (the user's answer-1: one close and reopen of #448 to start CI again at this head). next() honours it (hd.py ~1794: again = reopen(ch, head); 'if bad and not again'), so the change reaches a dev run for answer-1; but handover (hd.py ~2975: 'if (bad := failed_ci(ctx, ch, head))') refuses with 'upstream CI failed at 8c6d9679e ... never runs again at a head: commit a fix, or rebase onto main' without consulting reopen(ch, head). Every script row passes; the head is unchanged and main is still its base d30985ba3, so the dev can neither fix nor rebase: the change cannot leave the dev step and the reopen never reaches the card. Root cause: the hand-over and the pass each restate the CI-failure rule; one predicate (failed CI not answered by an unspent reopen at head) should serve both. Acceptance: with reopen: <head> unspent, hd handover at that head with all script rows passing succeeds and the card shows the close-and-reopen act; once the reopen is spent and CI still fails, handover refuses as now.
