---
slug: harness-dev-no-loop-build
track: harness
title: A harness dev running the loop's build verb by hand overwrites the loop's build
  record and build copy
kind: change
priority: P0
deps: []
created: '2026-11-01T00:12:45Z'
---
On the harness track 'tools/track.sh build <slug>' is the loop's verb: it writes state/<slug>/build.json and checks out the shared build copy .worktrees/<slug>-build. The dev brief (.claude/agents/dev.md:13: 'Build with <repo>/tools/track.sh build <slug>') tells devs to run it. Without T it fails ('empty string is not a valid pathspec' / 'invalid reference'), so devs passed a commit as the third argument; the record then lands in the live state with T empty. Evidence: state/harness-subject-row-range/build.json = {"T": "", "ok": true, "detail": "build copy .../.worktrees/harness-subject-row-range-build at df798e7b0"} while state/harness-subject-row-range/proc-build.json (the loop's) has TCOMMIT 5f71ad7dc and attempts 2; the loop's result was overwritten, so the pass saw no build for its tree, started another and raised 'harness-subject-row-range: build died twice without a result'. The manual run does not touch proc-build.json or build.log and kills no process, but it moves the build copy that a running gate of the loop reads. Fix so a dev cannot write the loop's records: the dev brief names the harness dev's own check (the unit tests in its worktree, or a track verb that needs no T) and track.sh build refuses without the loop's T/TCOMMIT env. One test per requirement touched.
