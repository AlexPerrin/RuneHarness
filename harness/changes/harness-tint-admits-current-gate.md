---
slug: harness-tint-admits-current-gate
track: harness
title: T_int admits a gated change by its gate at the current tree, not the hand-over's
  T
kind: change
priority: P0
deps: []
created: '2026-11-01T16:45:26Z'
---
integration() admits a server head only when (g[T]+'-').startswith(ho[T]+'-'), but nxt() calls a change gated when its gate is at the current tree. After the base moves, T is recomputed and re-gated while the hand-over keeps the old T, so the change reaches ship-test yet is left out of T_int; a pin conflict then finds no owner (owner = next change in heads at ship-test = None) and raises the planner alert instead of dispatching the owner's dev step.

Evidence (2026-11-01, base 2f8489f7e):
- genie-review-355: handover T 69fca5fb9b2a, gate T 9cfd0fe52b5e-b2bec4eeec99 ok; event 16:43:06Z 'test server deploy blocked by content/looting-bag's conflict'.
- cannon-review-354: handover T d4e3edca1923, gate T a06b77e3e3aa-b2bec4eeec99 ok.
- integration(ctx) heads: every pin plus server-world-entities only; conflict content/looting-bag 8c16a3073 (ObjTakePlugin.kt, after content/pirates-treasure), change None -> alert 'pin content/looting-bag conflicts ... a resolution ref or a change is needed' (planner-10 and planner-11 both spawned on it).

Fix: integration() uses the same gated test as nxt() (gate ok at the change's current key), one criterion in one place; ARCHITECTURE's 'T_int admits a gate whose key starts with the hand-over's T' updated. Test in the R8 class: a base move after the hand-over keeps a gated change in T_int and makes it the owner of a pin conflict.
