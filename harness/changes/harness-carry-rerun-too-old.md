---
slug: harness-carry-rerun-too-old
track: harness
title: A carry whose CI re-run is refused stops, and its next card cannot get the
  head a new CI run
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T07:21:05Z'
---
server-cache-clientscript-name-hash (#448), approved at 8c6d9679e on 2026-11-02 ~07:20Z: the carry's step 'gh run rerun --failed' was refused: 'run 41375908983 cannot be rerun; its workflow file may be broken' (the run is from the earlier carry; its failure was in 'Generate cache and gameval sources', a step the head reads, vouched by the dev's later hand-over). The new card drops the re-run step and only waits for CI at the head, which still holds that failed run, so a second yes would stop the same way. Acceptance: when a run cannot be re-run, the carry starts a fresh CI run for the same head (e.g. workflow_dispatch, or a re-run of the whole run) and judges that; the user's yes is never spent on a carry that cannot pass.

Also (filed): The carry's review request is refused (404): the account cannot request reviewers upstream
Monitor sweep 54 P1-a: AlexPerrin has push:false, triage:false on OpenRune/OpenRune-Server. The #354 carry's POST .../pulls/354/requested_reviewers (hd.py:2846-2847; reviewers Mark7625, a-thoren from hd.py:2636-2642) returned 'Not Found (HTTP 404)' at 07:35:09Z; state/cannon-354-...gIQ/ship.json records ok:false fault:carry after CI went green, the one comment posted and the PR marked ready. The card showed the user an act the carry cannot do. Same root as the refused CI re-run (no write access upstream). Acceptance: the card and the carry hold only acts this account can do; how to ask for review instead is the user's word (hd ask); a carry is never recorded failed for a step it cannot do.
