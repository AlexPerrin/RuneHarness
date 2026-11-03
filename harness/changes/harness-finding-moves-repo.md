---
slug: harness-finding-moves-repo
track: harness
title: A maintainer finding that moves a PR to another repo reaches the user, not
  a dev run
kind: change
priority: P1
mechanism: carry
deps: []
created: '2026-11-02T19:45:30Z'
---
Sweep 75 P2-a: Mark7625 on #448 (IC_kwDOQBbPT88AAAABiJnvhA, 19:43:04Z): 'could you please pr this to https://github.com/OpenRune/OpenRune-FileStore instead'. Triaged a finding (events.jsonl:11052), the pass filed server-448-cickwdoqbbpt88aaaabijnvha (11053) on the server track, but hd.yaml repos (4-7) has no FileStore and carry() (hd.py:3011-3068) pushes and comments only on the track's own upstream, so a dev run can neither do what was asked nor close #448 for a new PR. docs/PRD.md's workflow (maintainer feedback becomes changes on that PR) has no case for a move. The orchestrator held it with hd ask. Decide the mechanism: a triage verdict (or an ask the round opens with) that routes a move/retarget request to the user, and a way to add a target repo. Evidence: evidence/monitor/sweep-75.md
