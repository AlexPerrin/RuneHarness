---
slug: harness-server-content-passes
track: harness
title: A server change's verdict marks the content units it names as passing
kind: change
priority: P1
deps:
- server-content-inventory
goal: server-content
created: '2026-11-01T00:36:10Z'
---
harness/goals/server-content.md: "a row passes only by a verdict of a change that names the unit". Nothing implements it: grep of hd.py for "passes"/"server-content" finds nothing; the fork measure (~/src/OpenRune-Server/.worktrees/harness/tools/track.sh:139) only counts rows already flagged in the committed json, so the goal can never rise above 0 and every server change it plans stays unmeasured.

Give a server change a way to name its units (a field on harness/changes/<slug>.md) and make a passing verdict on a live change mark them; prefer measure deriving `passes` from the changes and their verdicts over hd writing the committed json. One test per requirement touched (R1); prove with a fixture change naming one unit.
