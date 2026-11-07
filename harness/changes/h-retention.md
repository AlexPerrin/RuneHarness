---
slug: h-retention
track: harness
priority: P1
---
# retention: every build artifact is released by the step that orphans it (docs/V9-RETENTION.md)

Implement docs/V9-RETENTION.md §4 (requirements 1-6) and its §5 KPIs: owner rows (kind,key,owner) in the store; release as a step of new head/close/merge/withdraw/run end, idempotent, ending on observed absence; one shared Gradle volume and one or-cache-store per input hash; docker builder prune when the last build of a T ends; disk facts (df of $HOME/src and /mnt/c) in the pass with an alert and no new build below the level; repair removes containers/.tmp/clones whose owner row is gone. A test per requirement. Remove the v8 per-slug gradle-<slug> volumes in tracks/fork/gate/gate.sh. Fold the requirements into docs/PRD.md and the rows/steps into docs/ARCHITECTURE.md, KPIs into V9-BRIEF §3b.
