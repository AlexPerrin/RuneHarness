---
slug: harness-limits-are-bugs-root-cause
track: harness
title: A change fixes its own limits; every fix is at the root cause, aligned
  with PROBLEM and PRD, rewrite allowed
kind: change
priority: P1
deps: []
created: '2026-11-01T21:27:06Z'
---
The user's word (2026-11-01): "all limits noted become bugs in general, changes need to consider the big picture. This is why PROBLEM and PRD always desribe the workflow in simplest terms, so we an make ARCHITECTURE changes without creating brittle systems. Issue should be identified at root cause, and the solution as a whole need be aligned, dont be afraid to rewrite."

Today showed the cost of the opposite: about forty harness changes, many patching the previous patch (tier hold -> hold-on-due -> hold-counts-only-listable -> running-holds-nothing -> listed-run-not-dropped; public flow -> fork queue -> console; ship records added, removed, re-derived), and limits left in hand-backs until the user asked for them to be filed.

Acceptance:
1. A limit is fixed in the change that has it, not passed on. A run does not hand over while its own change has a known limit in the mechanism it touched: it fixes it, or rewrites the mechanism so the limit cannot arise. Only a limit in a different mechanism (outside the change's scope) is filed, as one root-cause change for that mechanism (merged into an open change on the same mechanism if one exists, never a new change per symptom). This must converge: a change filed this way may not file another limit on the same mechanism; if its fix would, the two are one rewrite. The user's word on this item (2026-11-01): "Be careful this will fractal change indefinitely, the change itself should address these concerns." The hand-back lists any filed out-of-scope limit with its change slug; hd handover refuses a hand-back that names a limit inside its own scope.
2. dev.md, qa.md and planner.md say: find the root cause, state it against the PROBLEM/PRD workflow in its simplest terms, and fix it there, rewriting the mechanism when the cause is in its design rather than adding a special case; a fix that adds a rule on top of a rule names the rule it replaces.
3. The planner, on each run, reads the open harness changes and today's merged ones, and merges changes that patch the same mechanism into one root-cause change (closing the others by the user's word, or as superseded).
4. PROBLEM.md and PRD.md state the workflow (agents build a complete PR -> the user reviews it as text in the console and says yes -> it is carried upstream -> maintainer feedback becomes changes on that PR) in the fewest terms; ARCHITECTURE derives from them; the iteration protocol in CLAUDE.md says the same.
5. Tests: a hand-back naming an in-scope limit is refused; an out-of-scope limit merges into an open change on that mechanism instead of a new one.
