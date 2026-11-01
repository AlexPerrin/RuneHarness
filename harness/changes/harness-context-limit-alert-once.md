---
slug: harness-context-limit-alert-once
track: harness
title: The context-limit alert re-raises only on new limits, not on every close or
  count
kind: change
priority: P1
deps: []
created: '2026-11-01T05:30:57Z'
---
Alert (planner-2): the context-limit alert (hd.py dispatch(), line 809) counts a change's runs that reached the limit since its last handover, so once raised it stays raised until that change hands over. plan() re-lists the planner on it after every change close (handled resets at closed) and again whenever the count in its text moves (3 -> 4). The remedy is already filed and live (harness-brief-reads-once, c09fdfc), so each re-listing is a planner run with nothing to file.

Evidence:
- planner-1 (05:16Z-05:19Z) and planner-2 (listed 05:28:35Z) listed on the same two lines: "hunter-feat-pr: 3 runs reached the context limit without a handover ..." and "quest-runemysteries: 3 runs ...", inputs differing only in "last change closed" (05:15:52Z -> 05:28:28Z)
- planner-1 filed harness-brief-reads-once; it landed as c09fdfc before planner-2 was listed
- hd tick --dry-run at 05:3xZ: "alert: quest-runemysteries: 4 runs reached the context limit" after quest-runemysteries-5 (started 05:05Z on the pre-fix brief) hit 153617 tokens at 05:29:25Z: a third planner listing pending on a run whose brief predates the remedy
- hunter-feat-pr has had no run since 01:10Z (capacity, P3), yet its alert stays raised

Done when the count restarts at the later of the change's last handover and the last planner run that handed back on its alert, so the alert re-raises only after three more limits on briefs made after the planner's look; a change close alone does not re-list the planner on it. Test in the R class that owns dispatch alerts (R2/R6).
