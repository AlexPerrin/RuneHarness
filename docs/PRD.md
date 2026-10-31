# Requirements

The constraints every solution to docs/PROBLEM.md must satisfy, each derived from its principles. Code and tests cite the
ids. docs/ARCHITECTURE.md is the mechanism that meets each; docs/ACCEPTANCE.json is the checklist below as data, where
only `passes` may change.

| Id | Constraint | From |
|---|---|---|
| R1 **Goals** | Each goal is measured by its command whenever its target moves, shown with the tree it was measured on, and work is chosen to close the gap to its target. A server change unblocks the client once live on the test server. | P1 P10 |
| R2 **Flow** | A defined change reaches its live target with no person involved once the changes it depends on are live. Main is woken only to spawn an agent, show a card or relay the user's word; planning across tracks and the monitoring of operations belong to an orchestrator run listed by facts; nothing depends on either staying alive. | P3 |
| R3 **Contract** | What ships is exactly what was checked and approved, against a contract written before the code: the track's seed rows, the accuracy spec, the live upstream rules with their blob shas, the user's answers and prior findings. The hand-over passes every script row; the reviewer judges every row once, pass or fail, and verdicts append; a text-only failure is fixed in place. A gate is bound to the tree it ran on, a verdict and an approval to the head and contract they cover, each void when its input moves. A claim with no record counts for nothing; an unknown fact stops a step. | P1 P2 P7 |
| R4 **Authority** | Only a write to OpenRune and a client release need the user. No agent credential can do either; the harness does them only at the approved head. | P4 |
| R5 **Recovery** | Any failure is repaired in one pass with no user action; a repair is recorded only when its effect is observed, and one that recurs is raised once. Only what the user alone can decide or fix is raised, once per change. Nothing is decided from elapsed time. | P3 P5 |
| R6 **Economy** | A script runs before an agent, an agent before the user; nothing is checked twice for the same input; agents are bounded by one count; the pass acts and logs only when a change's state changes; a run hands off to a fresh run at the context limit; bring-up, scenarios and lookups are scripts. | P5 P8 P9 |
| R7 **Visibility** | `hd` prints what to spawn, the cards and questions waiting, what runs, each goal's number with its tree, and the facts of every open change, derived; nothing else. | P10 |
| R8 **Trees** | A change's tree T is its base, its dependencies and its head merged; a conflict is the dev's step, and a resolution against a permanent pin is a merge ref bound to both heads, used by the integration tree only. T is built at most once, in a copy no agent commits from; its artefact serves the dev's check, the gate, the review and the deployment. The game cache is rebuilt only when its inputs change. Every artefact and process is named after its change or run. | P6 P9 |

Constraints that need no mechanism: nothing contacts Jagex; the user's own RuneLite and the tester account are never
touched (A10). Each track's seed rows and the dev's and reviewer's rules live in each repo's `tools/track.md` and `.claude/skills/`.

## Acceptance

Each check is a command. `python3 -m unittest tests.test_hd.<R>` runs the requirement's class against fakes of git,
gh, docker and the process table; a live check reads the real state.

1. **R1** `tests.test_hd.R1`: a target move lists the measure step once; the measurement is bound to the target's tree;
   a server head live on the test server unblocks the client changes depending on it; below target with nothing open an orchestrator run is listed. Live: `hd` shows each goal's
   number with a tree equal to its target's current tree.
2. **R2** `tests.test_hd.R2`: a change with a live dependency goes from defined to live with no `approve`, `answer` or
   console call; `hd` lists a spawn exactly while an agent step is unmet and no run is alive for its input.
3. **R3** `tests.test_hd.R3`: a change without a contract lists the contract step and no dev; a hand-over with a failing
   script row, or whose pushed ref is not the head it names, is refused; a verdict missing a row is refused; verdicts
   append; a text-only fix leaves the verdict at the same head valid; a gate at T does not hold at T'; a verdict at H
   does not hold at H'; a moved upstream rule file voids only the rule rows; a failed fetch leaves every change where
   it was. Live: every `evidence/<slug>/contract.md` row has an id and a result.
4. **R4** `tests.test_hd.R4`: the upstream and release steps run only after an approval at that head. Live: `gh auth
   status` in an agent's shell shows the token scoped to AlexPerrin/*; `sudo -n -l` lists only the public-act helper
   under user `hd`; `hd approve` from a subagent is denied.
5. **R5** `tests.test_hd.R5`: console gone → its runs end and their artefacts are removed in one pass; a dead ship
   process → rerun; a yes recorded then main gone → the ship completes; a repair whose effect is not observed is not
   logged; the same repair twice raises once; a second `hd ask` on a change with an open question is refused.
6. **R6** `tests.test_hd.R6`: the same T never builds or gates twice; the same head and contract never judge twice;
   no more than the configured agents are listed; two passes over unchanged facts append no event; a run over the
   context limit is told to hand off and its successor is listed with the hand-off file; every run record carries
   its usage and transcript. Live: `tools/track.sh up <slug> 2` prints two logged-in clients' ports and returns.
7. **R7** `tests.test_hd.R7`: `hd` output contains only spawns, cards, questions, runs, goals and change facts, and
   prints no step name as a state. Live: `python3 hd.py` on the real state.
8. **R8** `tests.test_hd.R8`: T is `git merge-tree` of base, deps and head; a conflict lists the dev; a merge ref
   `local/merge/<a>-<b>` stands in for heads a and b in T_int and is ignored once either moves; build(T) runs once
   per T and in the change's build copy; the dev's clone is clean after a build; the cache step runs only when its
   input hash changes; every container, volume, clone and client window is named by its change or run. Live:
   `tools/track.sh build <slug>` twice prints `cached` the second time.
