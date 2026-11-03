---
slug: harness-start-reset-on-script-change
track: harness
title: A died-twice script is never retried after its track script is fixed, so both
  goals stay unmeasured
kind: change
priority: P0
deps: []
created: '2026-11-01T00:27:44Z'
---
hd.py start() (hd.py:443-461) resets the attempt count only when the args differ or a result landed after the last start. A fix to the track script itself changes neither: the args name the same goal and target sha. So after the measure fixes shipped, both goals stay stuck behind the alert and are never measured again.
Evidence:
- state/server-content/proc-measure.json: attempts 2, args [~/src/OpenRune-Server/.worktrees/harness/tools/track.sh, measure, server-content, 31241beef585...], ts 2026-10-31T23:34:45Z. The fix (harness-server-measure-goal-dir, fork a001a05ea) is live on local/harness: track.sh mtime 20:18:46 -0400, after the record. hd still prints "goal: server-content: measuring on 9a551147eaeb" and "alert: server-content: measure died twice without a result", and no measure runs.
- state/client-api/proc-measure.json: attempts 2, args [..., measure, client-api, d34b4f08d40e...], ts 23:34:43Z. The target sha is unchanged, so the same thing will happen when harness-client-measure-repo-root ships.
Fix: also start the count over when the script file (args[0]) is newer than proc-<name>.json, the same mtime comparison start() already makes for the result. One test per requirement touched (R5). Prove it with one real pass that starts server-content measure again.
