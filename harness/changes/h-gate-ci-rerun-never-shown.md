---
slug: h-gate-ci-rerun-never-shown
track: harness
priority: P2
---
# gate-ci waits forever on an infra re-run GitHub never shows

fork-friend-add-updates-list's gate (job gate ecb89c139683…:fork-1, pid 14299, started 2026-11-11T01:27Z) sat in tracks/fork/gate/gate.sh gate-ci for 2h+ with no result and no alert. Fork CI run 42939141541 (gate/fork-friend-add-updates-list, head ef196645df, revision 242) failed at 'Generate cache and gameval sources' at 01:31Z; infra() counts that step as openrs2's, so the loop waits on answers() and asks gh run rerun. GitHub still shows run_attempt 1, no re-run, and the loop (rr holds id.att, so 'GitHub has not yet shown it' → continue) polls every 30s forever. openrs2 serves the 242 cache (caches.json id 2757, disk.zip downloads). The failed step's log came back empty via gh run view --log-failed, so whether the step failed on openrs2 or on the 242 tree itself is unchecked. Done when a re-run that never appears (or a rerun request that did not take) ends the gate with a result, and a cache-step failure on the head's own revision is the head's, not infra.
