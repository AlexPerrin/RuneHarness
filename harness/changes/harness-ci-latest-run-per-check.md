---
slug: harness-ci-latest-run-per-check
track: harness
title: The CI wait reads only the latest run of each check
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T19:06:35Z'
---
Sweep 69 P1-a: the #448 carry (server-cache-clientscript-name-hash, pid 2623722) has hung since 18:18:22Z in the CI wait after the user's reopen; ship.log last says 'CI wait: failure: build & boot …runs/41375908983' while GitHub's new runs from 18:18:21Z are all green (build & boot 41499292032). F.ci (hd.py:456-465) returns every check run at the commit: the old failed build & boot (125055973126) sits beside the new success (125462312064), checks() (hd.py:2935) reports failure if any failed, and that failure is in the reopen's old set, so the wait (hd.py:3040-3044) neither raises nor succeeds and sleeps every 30 s forever. Undoes harness-ci-restart-same-head. Keep only the latest run of each check name; the hung carry must end and resume. Evidence: state/server-cache-clientscript-name-hash/ship.log, evidence/monitor/sweep-69.md

Also (filed): A carry hung in the old CI wait is stopped and resumed
Sweep 70 P1-a: the #448 carry pid 2623722 (hd.py ship server-cache-clientscript-name-hash 8c6d9679e, since 18:13:05Z) stays alive in the CI wait; start() (hd.py:1318) returns early for an alive script whose key is None, and a carry has no key, so a fixed hd.py never replaces it. The fix must end the hung carry and resume it under the new wait. Evidence: state/server-cache-clientscript-name-hash/ship.log, evidence/monitor/sweep-70.md

Also (filed): The commits a PR update's comment must name exclude those already on the base branch
unnamed() (hd.py) takes the commits the push adds as git rev-list head ^live-head (F.unmerged). When the update merges current main (#367: ce3177b6c merges origin/main 049a26312), that set holds every main commit the merge brings in (67 on #367, e.g. 011e3a108, d30985ba3 'Fix Discord server link in README'), which the push does not add to the upstream repo and the PR's diff does not show; the loop sends the dev back to name them all in pr-comment.md, an upstream comment no reviewer wants. Root cause: the pushed set ignores the PR's base. Fix: the commits to name are rev-list head ^live-head ^<upstream base ref> (the PR's baseRefName on origin, fetched), so a merge of main is named by its merge commit alone. Acceptance: a test where head merges a base commit absent from the live head; unnamed() lists only the PR's own commits (the merge included), not the base's. On #367 at def7f2c59 the comment then needs only ce3177b6c, ea08bce28, 08a6cc657, def7f2c59, which it names.
