---
slug: h-asks-recommended-autonomous
track: harness
priority: P2
---
# An ask is the user's only when a decision is the user's; the harness applies a recommendation itself

The user: they do not need to approve internal questions; the recommended option marks what the harness completes
autonomously. Today an ask is a human-only path: `hd answer` records `by = user`, refuses any `close` effect ("a close
is the user's own"), and the run waits until a person answers. Each ask of the 2026-11-11 batch (asks 1, 18, 30, 31, 32)
names a rule the harness lacks, so the run asked.

1. **Two kinds of ask.** `hd ask` takes a kind. `decision` is the user's, as today: an OpenRune upstream action, a client
   release, a permission, or options with no recommendation. `recommend` carries one recommended option and the evidence
   for it; the orchestrator applies that option at once (`answer.by = orchestrator`, every effect including `close` and
   `waive`, in the same transaction), the run is unblocked, and the ledger event shows the user the ask, the option and
   the evidence afterwards. The user may still reverse it with their own words. A `recommend` ask whose evidence does
   not name the artifact, change or criterion it rests on is refused by `hd ask`.
2. **Close the gaps behind the asks.**
   - A change whose product is outside git (a published jar, a config) finishes on that artifact: a submit kind that
     names the artifact and its check, instead of `hd submit` refusing a head that adds nothing to main.
   - A run can end its change as `done` (already fixed at a named commit) or `superseded` (by a named change) with the
     evidence, without an ask.
   - A criterion a blocker makes unjudgeable is deferred on its dependency (the `dep` effect) by the orchestrator, not
     asked.
3. **What does not change.** `hd approve` and the closing of a change the user did not leave to the harness stay the
   user's; a `decision` ask still blocks its run.

Update `hd ask`, `hd answer`, `hd submit`, the dev and orchestrator agents, the ask rules in docs/PRD.md and
docs/ARCHITECTURE.md (the ask and answer tables, the answer effects, `close (refused: the user's own)`), and a test per
rule: a `recommend` ask applies and unblocks, a `decision` ask waits, an artifact-only change finishes, a missing
evidence reference is refused.
