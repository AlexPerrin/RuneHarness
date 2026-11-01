---
slug: harness-no-runs-without-docker
track: harness
title: The pass lists no run that needs Docker while Docker is down; it alerts once
kind: change
priority: P1
deps: []
created: '2026-11-01T10:06:35Z'
---
After Docker Desktop died on the host (build log: 'error waiting for container: unexpected EOF'; then 'docker could not be found in this WSL 2 distro'), hd listed and the orchestrator spawned five dev runs (quest-restlessghost-11, quest-cooksassistant-8, server-world-entities-5, quest-ernestthechicken-5, quest-runemysteries-8); each read its brief and handed off within a minute with nothing done. Expected: the pass checks the observable fact (docker answers, e.g. 'docker info') once; while it does not, it lists no run whose next step needs build, up or test, raises one alert for the user ('Docker Desktop is down'), and lists them again when docker answers. One test per requirement touched.
