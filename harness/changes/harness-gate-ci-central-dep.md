---
slug: harness-gate-ci-central-dep
track: harness
title: gate-ci of a server change that depends on an unpublished Central version
kind: change
priority: P0
deps: []
created: '2026-11-01T13:12:46Z'
---
server-token-auth's head (fork dev/server-token-auth 7867a6340) bumps the server's Central dependency to 2.0.3, the version carrying central-token-login-op (the contract's one-change row requires it). build and test resolve it from the change's Central tree (server/central.init.gradle, harness-central-include-app, harness-test-central-include), but tools/track.sh gate-ci only pushes T to gate/<slug> and waits for the fork's CI, which resolves Central from the network: run 41308624734 on gate/server-token-auth at 7867a6340 fails 'Could not find dev.or2:central-common:2.0.3' (required by :engine:game), so the ci row can never pass before Central 2.0.3 is published upstream, and central-token-login-op's PR is held by the user until all login work clears. Needed: a gate of a change whose deps include a central change judges CI against that Central tree, e.g. gate-ci pushes the Central dev head to a gate ref and the gate tree (a local/ pin, never the change's head) gives the fork CI a step that checks it out and publishes it to mavenLocal (or includeBuild with server/central.init.gradle) before the build; the change's head stays unchanged. Check: tools/track.sh gate-ci server-token-auth at T of 7867a6340 concludes CI and Formatting green.
