---
slug: harness-gate-ci-index-per-run
track: harness
title: Concurrent gate-ci runs do not share one git index
kind: change
priority: P0
deps: []
created: '2026-11-01T15:27:44Z'
---
gate_sha() in the fork's tools/track.sh (local/harness, line ~271) builds the CI commit in GIT_INDEX_FILE=$(git rev-parse --git-path gate-index): one path per repo, so two gates at once collide and the ci row fails on a harness fault, sending the change back to dev.

Evidence (events.jsonl, state 'gate failed: dev', detail 'FAIL: ci: tools/track.sh gate-ci / fatal: Unable to create '/home/alex/src/OpenRune-Server/.git/gate-index.lock': File exists.'):
- 2026-11-01T14:20:49Z quest-sheepshearer
- 2026-11-01T14:22:40Z genie-355-bank-lamp, quest-cooksassistant
- 2026-11-01T14:54:58Z cannon-review-354, genie-review-355
- 2026-11-01T14:54:59Z quest-sheepshearer
- 2026-11-01T14:56:49Z cannon-354-return-after-destroy
Also: one gate's rm -f of the shared index can wipe another gate's index mid-build.

Done when: each gate-ci run uses its own index file (per slug or temporary, removed after), so parallel gates on the fork (and Central, if it shares the code) never collide; the tools test covers two gates at once. Carried on harness/<slug> of the fork's local/harness.
