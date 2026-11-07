---
slug: h-merge-conflict-retry
track: harness
priority: P2
---
# a staging merge conflict is retried when staging moves, not held on the head forever

decide.dev_due reads the last merge-conflict event and sends the head to its dev whenever the event names the tip (harness/decide.py dev_due, 'merge conflict on staging'); act.stage records only '<head7> <files>'. A conflict caused by staging (a pin, or a change since reverted) therefore keeps the head at its dev after staging has moved and the head would merge cleanly: the dev must make a new head to clear it (alert 45: e40d5e9 after 3d3a299). Done when the event records the staging tip it conflicted against and dev_due counts it only while staging is still at that tip, so a moved staging is merged again first, with a test in tests/test_decide.py.

## alert 45 fault 143 (×1, first 2026-11-07T04:57:01+00:00)
merge-conflict event for e40d5e9 (local/local-auth pin's ConnectionHandler.kt) keeps dev_due firing for that head forever: since 3d3a299 stage() reverts the pin first and e40d5e9 then merges cleanly (checked on a scratch copy of fork/staging), but dev_due precedes stage_due so the merge is never retried; the dev must make a new head
