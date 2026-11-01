---
slug: client-docs-no-bluestacks
track: client
kind: change
title: 'Client repo: BlueStacks references replaced by the Agent_Phone emulator (docs
  and scripts)'
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T22:33:11Z'
---
## Change
The user, 2026-10-25: "We migrated from BlueStacks to Android Studio at some point, remove old references to BlueStacks." The client repo still names BlueStacks (127.0.0.1:5555, Pie64, HD-Player) in README.md, docs/client-state.md, docs/plugin-host.md, docs/multi-client.md, docs/client-handoff.md, docs/offsets.md, docs/app-telemetry.md, tools/plugin-test.sh and tools/release-dev.sh. Replace them with the Android Studio emulator the agents use: the Agent_Phone AVD (Medium Phone profile, x86_64 API 37 with arm64 translation), addressed by ANDROID_SERIAL. Where a script defaulted to 127.0.0.1:5555, it requires ANDROID_SERIAL instead. Keep facts that are true of the client (the arm64-v8a-only native library); drop BlueStacks as a development device.

## Definition of done
- `grep -ri bluestacks` over the repo (outside re/ and build outputs) finds nothing.
- tools/plugin-test.sh and tools/release-dev.sh still run against an Agent_Phone emulator (one run of each, evidence in the evidence dir).

## Answers
- 2026-10-31T01:52:03Z console: server-openrune-http-sidecar-down added as a dep. When it lands, rerun the plugin-test.sh sign-in and hand over e8e9b0412.
- 2026-10-31T04:08:26Z console: the sidecars serve again (8080 and 8082 return 200; the change was closed). Rerun the plugin-test.sh sign-in on your own Agent_Phone and hand over e8e9b0412.
