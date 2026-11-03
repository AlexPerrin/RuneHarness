---
slug: harness-server-track-test-verb
track: harness
title: The server track runs the touched modules' tests and spotless
kind: change
priority: P1
deps: []
created: '2026-11-01T05:30:57Z'
---
quest-runemysteries-5 hand-back: the server track script has no test verb, so the dev ran gradle by hand in a container on the build copy to run its two new dupe test classes (the rule is builds through the track scripts); and spotless could not run in the container because it cannot open the git worktree, so formatting was checked by eye and left to the gate row. Expected: 'tools/track.sh test <slug> [module...]' runs the touched modules' tests (and spotlessCheck) on the change's build copy, with the worktree's git readable, and writes the result to evidence. Proof: track.sh test quest-runemysteries runs ArchmageSedridorTransactionsTest and AuburyTransactionsTest and spotlessCheck. One test per requirement touched. Also: that run kept helper scripts in the session scratchpad; evidence and helpers belong in evidence/<slug>/.
