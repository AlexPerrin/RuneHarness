---
slug: harness-done-needs-handover
track: harness
title: A dev ref with no commits counts as done
kind: change
priority: P0
deps: []
created: '2026-11-01T00:04:10Z'
---
After harness-ship-onto-live-branch (base = the live checkout's HEAD; live once the branch contains the change), harness-close-done shows 'done' while its dev run is still working: its dev ref harness/harness-close-done is at cbab2f2, v8's tip, with 0 commits ahead. A change is done only when a hand-over at a head beyond its base was shipped (or the user closed it), never because its fresh dev ref is contained in the base. One test per requirement touched.
