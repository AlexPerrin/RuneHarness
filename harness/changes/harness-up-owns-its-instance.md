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
sweep-42 P1-c: no agent sent server-npc-examine-without-overlay-6's stray input on desktop1:7780 (quick-prayer click, chat '/hi::item egg 1'); its only other user was server-clan-channels-4 (04:49Z, when 7780 was still its own) before npc-examine-6 claimed desktop1 at 04:51:11Z. Suspected: a desktop_login.py login or keep process left on 7780 by clan-channels-4's three overlapping ups/downs. One up at a time per slug; an up's login and keep processes act only on an instance whose owner is their slug, and end when the instance changes hands. evidence/monitor/sweep-42.md
