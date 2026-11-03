---
slug: harness-mechanism-required
track: harness
mechanism: contract
title: Every change names its mechanism; the one-change-per-mechanism rule is enforced
  on that fact
kind: change
priority: P1
deps: []
created: '2026-11-01T22:35:36Z'
---
Monitor sweep 5 (2026-11-01 ~22:17Z), a limit of harness-limits-are-bugs-root-cause (shipped a126161, PARTLY): mechanism() defaults to the change's own slug; no definition carries mechanism: or limit-of:; orchestrator.md never passes --mechanism/--limit-of; hd handover refuses only a limit the run names as limit:<slug>, so an unnamed limit passes. Evidence: harness-pass-lock-followup was filed as a new slug for harness-pass-lock-short's own limits, the pattern the rule forbids. Root cause: the mechanism is an optional free-text label, not a fact of each definition. Acceptance: hd new requires --mechanism (one of a short list in hd.yaml derived from ARCHITECTURE's components) and refuses a new change when an open change on that mechanism exists (it says which, so the filer merges); every open definition gets its mechanism; orchestrator.md files with it; the planner's merge step uses it; a test covers the refusal.
