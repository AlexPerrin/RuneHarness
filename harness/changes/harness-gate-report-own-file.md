---
slug: harness-gate-report-own-file
track: harness
title: the batch gate's suite report lands in a member's file
kind: change
priority: P1
mechanism: build-gate
deps: []
created: '2026-11-02T04:00:28Z'
---
sweep-32 P2-a: rowmemo writes the batch gate's whole test report to the first member's state/<slug>/tests.txt, which that member's dev 'track.sh test' then overwrites; it belongs under state/ship-harness/ (the gate's own). evidence/monitor/sweep-32.md
