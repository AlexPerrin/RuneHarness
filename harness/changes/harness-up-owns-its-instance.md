---
slug: harness-up-owns-its-instance
track: harness
title: 'a stray process drove another run''s desktop: overlapping ups of one slug
  leave login/keep processes on instances they no longer own'
kind: change
priority: P1
mechanism: desktop
deps: []
created: '2026-11-02T05:29:22Z'
---
sweep-42 P1-c: no agent sent server-npc-examine-without-overlay-6's stray input on desktop1:7780 (quick-prayer click, chat '/hi::item egg 1'); its only other user was server-clan-channels-4 (04:49Z, when 7780 was still its own) before npc-examine-6 claimed desktop1 at 04:51:11Z. The input came from quest-cooksassistant-14's own helper (evidence/quest-cooksassistant/qa14/qdt.py, PORT unset, default 7780) while its up was on 7781 (sweep-43); the endpoint answering any caller is harness-devtools-endpoint-owner's. The hygiene stands: one up at a time per slug; an up's login and keep processes act only on an instance whose owner is their slug, and end when the instance changes hands. evidence/monitor/sweep-42.md

Also (filed): desktop_login.py waits forever for an inventory that never arrives
sweep-43 P1-a: track.sh restart cannon-354-... (05:22:12Z) ran desktop_login.py 7782 (pid 2092911); the client reported LOGGED_IN at 3013,3452 and traffic flowed, but container 93 never arrived (no dynamicChildren on 9764864, list_inventories 0); the loop at tools/server/desktop_login.py:110-121 polls with no ending fact, so the restart hung ~20 min until the run brought the up down at 05:41:41Z. Login returns FAILED on an observed fact (N game ticks after LOGGED_IN with no container 93), never waits forever. evidence/monitor/sweep-43.md
