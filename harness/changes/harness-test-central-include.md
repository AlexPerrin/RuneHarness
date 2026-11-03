---
slug: harness-test-central-include
track: harness
title: The server track's test verb builds with the change's Central, as build does
kind: change
priority: P1
deps: []
created: '2026-11-01T12:27:25Z'
---
tools/track.sh test <slug> runs gradle without server/central.init.gradle, so a server change whose libs.versions.toml names an unpublished Central version (server-token-auth: dev.or2:openrune-central 2.0.3, the version carrying central-token-login-op) fails at dependency resolution ('Could not find dev.or2:openrune-central:2.0.3', evidence/server-token-auth/test.log) while build of the same T succeeds (or:1ea90ef99...-c0485930ffdf3). Needed: tests() mounts the Central worktree and the init script and passes --init-script /central.init.gradle with CDIR whenever CENTRAL is set, exactly as build() does. Also: tests() is piped through tail by callers, but its own exit already reflects ok; keep it. Related, for the gate: fork CI on gate/server-token-auth resolves Central from the network too, so the ci row cannot pass until Central 2.0.3 is published; decide how a gate with a Central dependency is judged.
