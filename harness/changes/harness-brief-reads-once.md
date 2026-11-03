---
slug: harness-brief-reads-once
track: harness
title: 'A run reads its change once: the brief and hd show do not repeat each other'
kind: change
priority: P1
deps: []
created: '2026-11-01T05:19:35Z'
---
Alert (planner-1): hunter-feat-pr and quest-runemysteries each had 3 dev runs reach the context limit (150000) without a handover. A large share of each run's context is its orientation reading the same text twice: the brief (hd.py brief(), line 769) embeds the hand-off, Definition, Answers and the whole Contract, then tells the run "Read <root>/tools/track.md, then run hd show <slug>", and hd show prints the definition, contract, the build's full gradle log tail and handoff.md again, plus every past run's last line.

Evidence (tool-result chars per run transcript, state/runs/<run>.json transcript):
- hunter-feat-pr-4: `cat state/briefs/hunter-feat-pr-4.md` 29429 (Contract section 19997); `cat track.md; hd show hunter-feat-pr` 29698; then `hd show hunter-feat-pr | sed -n 150,400p` 9723
- hunter-feat-pr-3: brief 29172; track.md + hd show 8218
- quest-runemysteries-4: brief 15023; track.md + hd show 24125
- quest-runemysteries-3: brief 13574; track.md + hd show 22915
- quest-runemysteries-2: track.md + hd show 16548
- hd show quest-runemysteries prints the build detail as ~3000 chars of gradle warnings; hd show hunter-feat-pr ~2500 chars of gradle task lines on a successful build
- context-limit events in state/events.jsonl: 18 since 2026-11-01T00:48Z across 11 changes (hunter-feat-pr x2, quest-runemysteries x3, cannon-review-354 x2, goblin-diplomacy-review-367-fftgsrq x2, quest-restlessghost x2, ...)

Done when a run's orientation carries each of hand-off, definition, answers and contract once (either the brief alone, or hd show alone), the build line is its verdict and image (the log stays in a file it names), and the dev/qa/planner roles and track.md say the same. Test in the R class that owns briefs.
