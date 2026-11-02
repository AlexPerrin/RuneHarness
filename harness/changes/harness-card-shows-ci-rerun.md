---
slug: harness-card-shows-ci-rerun
track: harness
title: a card does not show the CI re-run its yes triggers
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T04:22:33Z'
---
sweep-34 P2-b: the name-hash card lists update / wait CI / comment / ready and 'the last carry ... stopped ... the PR stays as it is', while the carry would run gh run rerun --failed (hd.py:2668); carry()'s docstring says the act runs exactly as its card shows it (hd.py:2694). The card names the re-run as its own act. evidence/monitor/sweep-34.md
