---
slug: harness-tools-no-pycache
track: harness
title: Compiled Python caches are committed on the fork's tools branch
kind: change
priority: P2
deps: []
created: '2026-11-01T00:07:10Z'
---
Fork local/harness commit f4f90c43b (harness-jav-config-local-only) adds tools/server/__pycache__/javcheck.cpython-312.pyc and test_tools.cpython-312.pyc. Remove them and ignore __pycache__/ on local/harness (and client/harness-v8).
