# ISSUES

The open ledger of the v7 run, cleared at the hand-off on 2026-10-25. A quick fix lands at once and is not logged (git
history has it). What lands here is what a quick fix does not settle: a root cause in the design, or a rewrite too large
for the run. Each entry is what happens, why, and what v8 should do; newest first. The v8 iteration reads this with
docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md and questions all four.

## Open

- **Smaller faults found 2026-10-31** (not in docs/V8-BRIEF.md): a change whose dep was deleted blocks with no message;
  the guard refuses an `hd ask` whose text quotes a push command; an integrator's note-only `hd ask` reaches the user as
  a question; a definition of done is not rewritten when a scope answer changes it (hunter, clans); the session
  devtools assume port 7780 and mobile needs `ANDROID_SERIAL` set; the pass refuses to merge a harness change while
  another session has uncommitted docs edits. v8: each is a fact the owning step checks, not a rule an agent recalls.

- **Review does not converge.** The four upstream review changes took 77 of 131 runs and 41 of 66 agent-hours
  (goblin-367-fftgsrq: 23 runs, 8 QA rounds). Each QA round confirms the previous findings fixed and then finds new
  ones (goblin 4, 2, 1, PASS, 4, 6, 4; hunter 9, 5, 5, PASS, 10, 5), and several rounds failed on PR text alone, at
  the cost of a full dev and QA run. Why: QA stops at what it finds first and checks nothing against a fixed list, and
  only the latest `verdict.json` is kept, so findings per round cannot be measured. v8: QA runs one fixed, exhaustive
  checklist per change (accuracy spec, live AGENTS.md rules, PR text) before its first verdict; the dev checks the same
  list before hand-over; every verdict is appended, not overwritten; a text-only finding is fixed without a new QA run.
  Devs also leave findings open: goblin round 9 failed on two repeats (PR text "not fixed"; game data in Kotlin fixed
  for the `MailDye` enum, then back as `ARMOURS`), because a finding is fixed where it was named, not as a rule across
  the commit. v8: the hand-over records each prior finding with the rule it breaks and the check that proves it
  closed across the whole diff.
- **Agents run at the top of their context.** Average context per turn: server-dev 222k, client-dev 187k, server-qa
  144k tokens (4.1B cache-read tokens over 22k turns). Why: dev runs read the evidence, logs and decompiled code
  themselves instead of through subtasks. v8: read-heavy work goes to subtasks by default, and context per turn is a
  measured number.
- **The event log is mostly repeats.** 764 of 1174 step events repeat the change's previous step and detail (the
  pass logs `queue: train running` and `gate pending` on every tick). v8: log a step only when it changes.
- **A client build reached Jagex's servers.** Run `client-devtools-menu-actions-3` repacked without `OPENRUNE=1
  LOCAL_AUTH=1`, so the APK kept Jagex's jav_config, RSA modulus and AppAuth endpoints; on the emulator it very likely
  fetched Jagex's jav_config and world list and opened account.jagex.com in Chrome (no sign-in). The brief's build line
  and the "7 telemetry lines" check pass a stock-server build too. The guard now refuses a plain repack and the client
  gate wants the test-server patch lines; v8: no APK is installable without those lines in its repack log, checked at
  install, not only at the gate.
- **A pass change goes live on upstream within a minute.** The timer runs `main`, so a commit that changes an upstream
  step acts on real PRs at the next tick: twice on 2026-10-25 a rule committed before its dry run put a PR in a wrong
  visible state (#355 drafted, #367 marked ready for a minute). Until v8 the console pauses the pass
  (`harness/state/paused`) and dry-runs against the live PRs before committing such a change. v8: a change to an
  upstream step is dry-run against the live PRs by the harness's own gate before it can be merged.
- **Stale pinned branches stay in integration until a person drops them.** The v6-era entries of `integration.txt`
  (`fix/*`, `content/*`, `local/*`) belong to no v7 change, so nothing removes them when they rot against upstream main;
  each rot is an integrator run. v8: every pinned branch belongs to a change or to the fork's permanent local list, and a
  branch leaves integration by a fact (its change is gone), not by a resolution.
- **Throughput is bounded by the console.** Agents are spawned by hand with the Agent tool, so listed spawns wait for the
  user's presence, and a paused agent holds one of three slots. Measured from the record that makes a run due (gate,
  verdict, answer) to its start: median 11 min, p90 83 min, worst 534 min (105 spawns). v8: decide whether the pass
  may spawn.
- **The guard judges command text.** A local `git remote set-url` naming upstream was denied while the pass's own
  `gh pr ready` runs outside the guard. v8: judge by effect only (the remote resolved at push time, the repo named to
  gh).
- **The brief's first line is a protocol between three programs** (steps writes it, the Agent prompt carries it, the
  hook parses it back). v8: the spawner writes the run record; nothing is parsed out of a prompt.
- **Repairs find orphans by the v7 run name.** Artefacts of earlier versions (v6 clones, state) are invisible to them
  and were removed by hand; client windows carry no owner at all, so one left by an ended run stays open until a
  person notices (desktop, 2026-10-25). v8: name every artefact after its change, clients included, and remove it when
  the change is done.
