---
slug: harness-test-verb-default-modules
track: harness
title: track.sh test with no module names the touched modules
kind: change
priority: P1
deps: []
created: '2026-11-01T07:02:33Z'
---
quest-ernestthechicken-3 hand-back: 'tools/track.sh test quest-ernestthechicken' with no module named fails within seconds; naming the modules (':content:quest' and the Draynor module) works. harness-server-track-test-verb defined the no-module form as 'every module holding a file the change modifies relative to origin/main'. Expected: the no-module form finds those modules and runs their tests and spotlessCheck; on a failure it prints why. Proof: track.sh test quest-ernestthechicken with no module runs both touched modules. One test per requirement touched.
