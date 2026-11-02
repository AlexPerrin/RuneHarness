---
slug: harness-filestore-track
track: harness
title: 'OpenRune-FileStore is a target track: fork, clone, tools branch and gate'
kind: change
priority: P1
mechanism: build-gate
deps:
- harness-attempts-test-mtime-flake
created: '2026-11-02T21:00:26Z'
---
The user (2026-11-02, answer to server-448-cickwdoqbbpt88aaaabijnvha): '(a) add OpenRune-FileStore as a target repo, port the fix as a new PR there and close #448 pointing to it' after Mark7625 asked on #448 to 'pr this to https://github.com/OpenRune/OpenRune-FileStore instead please so its built into current cs2 system'. hd.yaml repos has no FileStore entry. Needed: the fork AlexPerrin/OpenRune-FileStore (forks are free), its clone, an hd.yaml repos entry with upstream OpenRune/OpenRune-FileStore, and a tools branch with tools/track.sh (build, gate rows against FileStore's CI and its AGENTS.md/CONTRIBUTING/PR template) and tools/track.md, so a change on that track builds, gates and carries a PR there. The orchestrator commits the hd.yaml entry the run names.

Also (filed): The server test verb runs integration only where the task is registered
Sweep 84 P2-a: server tools dd863ba52 (fork local/harness tools/gate/gate.sh:46) adds $d:integration whenever a module has src/integration, but only modules applying the integration-test-suite plugin (build-logic/src/main/kotlin/integration-test-suite.gradle.kts:11) register it; 14 modules on origin/main have src/integration without the plugin (api/cache, api/game-process, api/inv-plugin, api/invtx, api/player, api/repo, api/shops, api/stats/xpmod, content/interfaces/bank, combat-tab, emotes, woodcutting, travel/canoe, ...). A qualified :api:invtx:integration fails task selection even with --continue (upstream CI's bare 'integration' skips projects lacking it, .github/workflows/ci.yml:72), so track.sh test on a change touching them fails falsely. Decide on the registered task, not the directory. Evidence: evidence/monitor/sweep-84.md
