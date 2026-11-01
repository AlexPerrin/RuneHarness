---
slug: harness-pin-base-conflict
track: harness
title: 'integration tree: a pin that conflicts with the base gets a resolution path'
kind: change
priority: P0
deps: []
created: '2026-11-01T02:08:22Z'
---
A permanent pin that conflicts with the fork base itself (not with another included head) has no resolution path: tint() tries local/merge/<a>-<b> refs only against heads already included, so the alert 'a resolution ref or a change is needed' can be met by neither, and every server change's test server deploy stays blocked.

Evidence:
- events.jsonl 2026-11-01T02:05:25Z: genie-review-355 [server P0] 'test server deploy blocked by fix/22-music-tab-play's conflict'
- hd alert: 'pin fix/22-music-tab-play conflicts with the integration tree (fix/69-blue-moon-inn-stairs, fix/10-login-welcome-message, fix/11-dense-clientscript-ids): a resolution ref or a change is needed'
- git merge-tree --write-tree fork/main fork/fix/22-music-tab-play (8b3cfaca4) conflicts alone, in api/music-plugin/.../scripts/MusicTabScript.kt; fork/main touched it in 1f23d586c 'Fix Area music activation and Shuffle Skip (#400)'. The pin is unchanged since 2026-10-18; the base moved.
- hd.py tint(): the resolution loop iterates 'included' only; the base is never a resolution partner. ship_test() dispatches a dev only when the conflict is a change's.

Done when: a pin conflicting with the base (or with an included head) leads to an owned step without the user (a dev run that records a resolution the integration tree uses, bound to the pin head and the base it was made on), and genie-review-355 reaches its test server deploy. Whether fix/22 is superseded by #400 is that dev's finding, reported, not a pin-list edit (the pin list is the user's).
