# V8 brief

What v7 actually did, measured from its own records (harness/state: events.jsonl, runs/*.json and the agents'
transcripts, 2026-10-25 → 2026-10-31: 132 runs, 14.5k tool calls). Read it before docs/PROBLEM.md, docs/PRD.md and
docs/ISSUES.md. docs/ARCHITECTURE.md describes v7 as it was built, legacy logic included: reference only, not a spec.
Goal of v8: the same outcomes with the fewest concepts, files and lines, and more throughput per token.

## 1. Keep (the constraints, by id)
- PROBLEM axioms A1–A10 and principles P1–P8; PRD R1–R7. The user's rules: CLAUDE.md "Rules" and "Shared rules", and
  the memory index `~/.claude/projects/-home-alex-osrs-harness/memory/MEMORY.md`.
- Goals. Client: % of RuneLite API interface methods working in the app, by probe (`tools/api-probe.sh`, 60.9/100).
  Server: 1:1 with the official game, the client never blocked; **no metric exists**: v8 defines one (an inventory of
  content units from the cache, each checked against RSProx recordings and the wiki, with a pass flag).
  Harness: simpler and faster each iteration; measured by §3's numbers, which v8 must beat.

## 1a. New requirement: R8 Build (from P2, P6)
A server build is a function of one tree, **T = upstream base + the change's dependencies + its head** (computed by
`git merge-tree`; a conflict goes to the dev before anything builds). Each T is built once, and dev check, QA, gate
and test-server deploy all use that build. The game cache is its own artefact, keyed by its inputs, built and
verified only when they change. A gate is keyed by T: an upstream move re-gates only if T changes. Only three events
make a new T: a commit, an upstream move, a dependency change.
Workflow: pin → T → build(T) → up(T, accounts) → dev loop (each edit is a new T, built incrementally) → hand-over at
T → gate(T) → QA on the same build → verdict(T); integration = base + all pins is its own T, built once and deployed.
Measured waste R8 removes: ~72 min of identical-tree builds, ~97 min of cache re-downloads, ~27 min of cache steps
with unchanged inputs, ~219 CI min of re-gates on unchanged heads, and by-hand dependency trees (clans dev, 10-31).

## 2. The workflow as it ran
One loop over five nouns: **change** (definition) · **commit** (head + base) · **judgment** (hand-over, verdict,
approval, answer; bound to head + base) · **target** (where live means) · **run** (role, change, start, end).
`next(change)` = first unmet of: dev commit → script gate → agent verdict → user's yes (public acts only) → ship →
wait on the outside world. Nothing else needs to be stored.

Where a change's life went (35 changes):

| State | Share |
|---|---|
| waiting on maintainers | 30% |
| due for a spawn (defined, after a FAIL, an answer or a gate fail) | ~30% |
| queued for the train (runs alongside review; partly overlap) | 21% |
| waiting on the user | 10% |
| CI | 4% |
| **agents working** | **5%** |

## 3. Numbers v8 must beat
| Metric | v7 |
|---|---|
| runs per upstream PR | 15–23 (4 PRs = 77 of 132 runs, 41 of 66 agent-hours) |
| QA rounds per PR | up to 9; findings per round goblin 4,2,1,PASS,4,6,4,2 |
| spawn wait after the record that makes a run due | median 11 min, p90 83, max 534 |
| context per turn | server-dev 222k, client-dev 187k, server-qa 144k |
| tool calls before first edit | server-dev 81, client-dev 52, server-qa 148 |
| share of calls that are sleep/until polling | 12% (server-dev 946 sleeps, client-dev 683) |
| subtask calls by server-dev | 0 |
| guard denials judged wrong | ≥ half of 40 |
| step events that repeat the last one | 764 of 1174 |

## 4. What failed, and why (the root causes)
1. **Review has no contract.** QA finds new defects every round, and devs fix a finding where it was named, not as a
   rule across the diff (goblin: `MailDye` enum fixed, `ARMOURS` list next round). PR-text-only fails cost a full dev
   and QA run each. Only the last `verdict.json` is kept. → QA and dev agree a fixed checklist (accuracy spec, live
   AGENTS.md rules, PR text, in-game) before coding; each item pass/fail; verdicts appended; text fixed without a new QA run.
2. **Know-how is prose, so agents re-derive it.** Bring-up of build, server and client is in skills, executed by hand
   every run (52–148 calls before work, 12% polling). Four of five agent retros independently ask for the same
   tool (`qa-run`, `hd up`, `qa-session`, `branch-session`): clone and merge onto the gate's base, build, start the
   server on free ports, seed accounts (members, dev_mode), start and log in N clients, print ports, block until
   ready, and stop it all (retros goblin-23, hunter-16, hunter-18, friends-chat-11). → that one script per track,
   plus a `wait-for <fact>` tool, a dialogue driver and a `gameval <table> <name|id>` lookup over every table;
   skills keep judgment only.
   Transcript sweep (82 server runs; phase share of time, dev / QA): waiting 23% / 14%, code 17% / 13%, in-game test
   16% / 27%, build 13% / 1%, client start and login 9% / 13%, orienting 6% / 10%. 252 build calls (188 repeats:
   50 after an edit, 58 with no error between, 24 dirty `.data/gamevals`, 11 stale cs2, 10 missing base ref);
   215 client start/login calls (158 repeats, 45 after "not ready"; ~320 min); ~30 waits end at ~9.3 min, the
   Bash timeout, then loop. Only code + in-game test (~33% dev, ~40% QA) is the work itself.
   Client (29 client-dev runs): no same-commit rebuilds (each followed an edit or merge; build median 144 s). The
   cost is the device: 887 Bash calls drive adb by hand; WSL interop timeouts (accept4 failed 110) in 28 results;
   login hangs to the 9-min timeout (~40 min), 51 login calls; emulator boot waits to 6 min; 16 of 32 restore checks
   not OK; 322 screenshots despite the data-tools rule; 674 sleep commands. → the client bring-up (emulator boot,
   install, login, restore) is one script that blocks on facts, run Windows-side so no call crosses WSL interop.
3. **Agents read at full context.** Read-heavy lookups (RSProx, cache, decompiled code, logs) are done in the agent's
   own context. → those become scripts or tools that return conclusions.
4. **The guard judges command text.** It blocks reads and evidence writes that mention upstream words, and lets the
   pass act unguarded. → authority by credential or effect, not by parsing.
5. **Spawning waits on the console** (§3). → decide whether the pass may spawn.
6. **A gate PASS survives a change of the gate.** Re-gating keys on head and the change definition hash
   (`hd/steps.py:629`), not the gate's own version, so a stricter gate does not re-check gated commits.
7. **A pass change acts on upstream within a minute** of landing on `main` (twice put a PR in a wrong state).
   → a change to an upstream step is dry-run against live PRs before it merges.
8. **The instructions rot and contradict, and agents can't see it** (retros):
   - Dead pointers: server-qa.md:8 and pr-text-review:7 cite a QA.md that does not exist; build-test and
     test-instances give a wrong qa.sh path; instance.sh is not executable; desktop.sh clicks fixed-mode spots and
     fails in resizable mode.
   - Rule clashes: the brief's "one commit off upstream main" vs a change on an existing PR branch; "FAIL any
     unticked item" vs a gap the user accepted (hunter's wiki item, so FAIL by rule every round); "default no tests"
     vs upstream AGENTS.md's dupe tests.
   - Monolithic skills: server-track's integrator section and test-instances' Android parts are noise for others.
   → v8: instructions point only at scripts that a test runs (a dead path fails CI); one file per role; each user
   answer amends the checklist, not a free-text Answers section.
9. **QA can test the wrong base.** `qa.sh clone ... main` merged onto the shared clone's stale local main
   (c2492318d, not upstream 31241beef); goblin-23 re-merged by hand. → the bring-up merges onto the gate's recorded
   base, never a local ref (R3).
10. **No agent can read the previous verdict** (`hd show` is missing; 26 failed calls), so "close every prior finding
   first" is not a step, and repeats follow. → a read command, and the checklist's first line.
11. **The shared cache download is discarded almost every run.** 36 of 49 cache steps re-downloaded the OpenRS2
   cache (97 min); 35 first logged "Cache corrupted or incomplete. Deleting .../caches/oldschool/241", so the
   shared volume `openrune-dl-cache` is not reused (only 12 reuses, all 10-25 23:52 → 10-26 03:12). The message
   comes from a dependency, not the fork's source. Cause: `gate-steps.sh` publishes to the store by revision
   directory (`/dl/caches/oldschool/241`) and skips publishing when that directory exists, while the library
   checks the cache id inside it. When OpenRS2 publishes a new cache id for the same revision (2746 → 2752 on
   10-30), every build seeds the old `2746-disk.zip`, the library judges it incomplete, deletes it and downloads
   2752, and publish skips because `241/` exists: a permanent miss until someone clears the store. The same
   pattern ran 10-21 → 10-25 with the previous id. → key the store by `<id>-disk.zip` and replace a stale id. Also: the
   cache step ran with no change to its inputs in 10 of 33 train gates (~27 min). Build sweep: 34 train gates
   (438 min, 9 failed: 8 gameval id clashes between merged branches), 10 QA gate-runs, 63 fork CI runs (~14 min
   each, 838 min); ~72 min spent building identical trees twice (e.g. world-entities f2a808495 built as `or/`
   and `run/` with nothing merged in; two train gates of the identical tree eab9908af).
   Gates: 49 fork CI dispatches over 35 heads, 811 run-minutes; 14 were re-gates of an unchanged head caused only by
   an upstream move (~219 min, 27%); goblin-367 gated one head 7 times; three upstream moves in 4 min cancelled 2
   runs. Train: 47 starts → 22 deploys; 8 rebuild conflicts, 7 silent exits (overlapping trains), 10 gate fails; gate
   median ~850 s; one train rebuilt a tree identical to the previous one (likely a race on live.json). Integrator
   (15 runs): conflicts and gameval clashes mostly between two pinned changes, not with upstream; one wrong recorded
   resolution caused a later failure; one "conflict" was a stale MERGE_RR.lock from an overlapping train.
   → v8: a gate is keyed by tree (re-gate only when the merged tree changes); pins conflict-checked against each
   other when pinned, not at train time; one train at a time by construction.
12. **Every run builds the change twice.** The dev's tree (`qa.sh dev`, persistent container) and a merged tree
   (`qa.sh gate-run`, fresh container, `clean` first) each compile and rebuild the game cache (~3 min each); a
   shared download volume still re-downloaded 213 MB when found incomplete. → one build per (head, base) in the
   bring-up script, reused by dev, QA and the gate; the cache artefact keyed by cache id and verified, never rebuilt
   per tree.
13. **Shared tool side effects:** `qa.sh dev`'s cache step dirties tracked `.data/gamevals`, and 3 runs restored it by
   hand. → the build leaves the tree clean, checked.
14. **Wide, long-lived PRs reopen findings** (hunter: ~75 files; each feature adds data lists; gamevals renumbered
   against other branches). → a size bound per change, measured.
15. **The pass repeats work with no state change.** Per pass-sweep: 467 gate-pending polls (357 identical, each a
   CI API call), 202 gate records re-saved for an unchanged head, 432 identical "train running" lines, and the same
   volume repaired 68 times (gd17-dev-gradle): a repair that never converges. → act and log on edges only; a repair
   that recurs is a bug, raised once.
16. **The pass merges into a shared working tree.** Any session's uncommitted edit in ~/osrs-harness stops every
   harness merge (the monitor's draft blocked harness-dupe-check, 2026-10-31). → the pass merges in its own clone.
17. Also open in docs/ISSUES.md: a client build reached Jagex (no install-time check of the repack log); stale pins in
   integration; the brief's first line parsed by three programs; orphans found only by v7 run names.

## 5. Component ledger: cut, merge, keep
Use = agent tool calls naming it (runs); pass-side use from events. Full per-file table: `evidence/monitor/ledger.md`
(regenerate with `evidence/monitor/ledger.py`). Rules: unused and no R needs it → cut; done by hand → script;
several doing one job → merge; patched often → rewrite, don't port.

| Component | Lines | v7 use | Verdict |
|---|---|---|---|
| `hd/steps.py` | 747 | the pass; 19 commits, 3 fixes since 10-25 | rewrite as `next(change)`; merge, ready, comment, push and title (55 events in all) become one upstream step |
| `hd/` rest (cli, facts, tick, store, server) | 925 | agents use 5 of 9 commands; 26 calls to non-existent `show`/`status` | one module; add the one read command agents look for |
| `hd/dashboard.py` | 127 | 0 agent use; 125 errors on 10-26 | derive from `hd`'s output or cut (R7) |
| `hooks/hook.py` + `shellparse.py` | 543 | 40 denials, ≥ half wrong | replace by credential authority (§4.4); keep run start/stop records |
| `gates/gameval_ids.py`, `gates/server.py` | 326 | 30 and 6 runs | keep (scripts before agents) |
| `gates/client.py`, `gates/harness.py` | 92 | 2 and 0 runs | merge into one gate per track |
| `train/` | 327 | 46 starts, 6 failures, 15 integrator runs averaging 7 min | keep as a script; pins belong to changes; add `record-resolution` so the integrator only edits the conflict (retro friends-chat-8) |
| `bench/multiclient/desktop.sh`, `desktop-devtools-mcp.sh`, `instance.sh` | 174 | 64, 62, 48 runs | merge into the bring-up script per track |
| `bench/device-restore-check.sh`, `emulator_login.py` | 208 | 26, 8 runs | merge into the client bring-up |
| `bench/multiclient/headless/*`, `make_proxy_target.sh` | 236 | 0 | cut |
| `mcp/` devtools front (`devtools_bridge.py`, 1,086-line snapshot) | 1,180 | devtools-mobile MCP 0 calls, desktop 68, vs 464 calls to the bash bridge | pick one path to the client (the data tools), cut the other |
| `osrs-mcp` (cache, wiki, gameval) | 17 | 689 calls | keep: the most-used tool |
| roles (7) | 230 | orchestrator 3 runs, integrator 15, harness-dev 1 | dev and QA per track; the orchestrator and integrator as steps or modes |
| skills (13) | ~550 | mentioned in: test-instances 94 runs, server-track 79, build-test 66, accuracy-check 47, pr-text-review 47; ab-test 2, network-qa 5 | one rules and checklist file per role (retros: integrator, Android and gate-internals sections are noise to others); procedures become scripts |
| `docs/ARCHITECTURE.md` | 348 | 19 commits since 10-25 | rewrite: what the code does, derived; one page |
| `docs/evidence/`, `harness/state.v6/`, `harness/retired/` | — | legacy | cut |
| `tests/test_hd.py` | 661 | 48 commits in October | one test per R, against the new loop |
