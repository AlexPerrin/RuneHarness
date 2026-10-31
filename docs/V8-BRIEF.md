# V8 brief

What v7 actually did, measured from its own records (harness/state: events.jsonl, runs/*.json and the agents'
transcripts, 2026-10-25 → 2026-10-31: 132 runs, 14.5k tool calls). Read it before docs/PROBLEM.md, docs/PRD.md and
docs/ISSUES.md. docs/ARCHITECTURE.md describes v7 as it was built, legacy logic included: reference only, not a spec.
Goal of v8: the same outcomes with the fewest concepts, files and lines, and more throughput per token.

## 1. Keep (the constraints, by id)
- PROBLEM axioms A1–A10 and principles P1–P8; PRD R1–R7. The user's rules: CLAUDE.md "Rules" and "Shared rules", and
  the memory index `~/.claude/projects/-home-alex-osrs-harness/memory/MEMORY.md`.
- Goals. Client: % of RuneLite API interface methods working in the app, by probe (`tools/api-probe.sh`; about 93% at client master 6cc6bbe, though `hd` still shows a stale 60.9, §4.18).
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

## 1b. The driver: the user's primary chat (main)
Main is the user's chat and the only session that can spawn agents (A2). Both jobs collide: 53 of 56 long spawn waits fell while the user and main were mid-conversation (main acts only at a turn boundary), and harness traffic fills main's context (51 spawns pasted 149k chars of briefs; hand-back reports in full; main compacted twice on 10-31, each time losing the run's state). The interface:
1. **Spawn by path**: the prompt is one line, "Read and follow <brief path>"; the agent reads the brief.
2. **Hand-back as one line**: `run X: handed over <sha> | FAIL 3 findings → <path>`; the full report is a file the pass reads.
3. **Event-woken, one step**: a watch on the harness's events wakes main when `hd` lists a spawn, card or question; main makes that one background call and returns to the user.
4. **Long work leaves main**: investigations, harness changes and reviews go to subagents or a side session, so main's turns stay short and spawns never queue behind a conversation.
5. **Main holds no state**: after a compaction or restart, `hd` rebuilds the picture from files; compaction costs nothing.
6. **The user sees only what needs them**: cards, questions that need a decision (§4.19), one-line notices, the goal number measured when a change goes live (§4.18).

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
| context | starts at ~35k; peak median server-dev 160k, server-qa 189k, client-dev 207k; max 887k |
| model time per run | 39–51% of wall time is the agent choosing its next step (median 5 s per turn) |
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
   Classified (23 FAIL rounds, 108 findings): accuracy 34, PR text 33, upstream rule 23, functional bug 14, process
   4. 68 repeat an earlier round's rule or defect (PR text 25 of 33, rules 17 of 23). Every rule and text finding
   (60) was catchable by a checklist row written before coding; accuracy and bugs partly. Seed rows, by count:
   (15) every PR claim and ticked box true of the exact head; (11) timings, steps and messages checked against
   RSProx recordings tick by tick first; (10) no deferral: no Not-done list, no unticked item, or `hd ask`; (8) on an
   existing PR, pr-comment.md covers only the net change since the live head; (7) the unsourced list names every
   reconstruction and cheat; (6) no game data or raw ids in Kotlin; (6) every flow playable without a cheat.
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
   Measured: every run starts at ~35k tokens (prompt, role, CLAUDE.md, tools) and peaks at a median 160k (server-dev), 189k (server-qa), 207k (client-dev); max 887k. Tool output totals ~6M tokens, but each is re-read every later turn: weighted by turns remaining, reads with cat/sed/head are 28%, grep/find 20%, git diff/log 12%, cache/wiki lookups 8%, devtools 8%. No single file dominates; the harness's own scripts and skills re-read each run (desktop.sh 72 reads, qa.sh 58, build-test 55, test-instances 23) are ~4%. → shorter runs with a hand-off file (cost grows with run length squared), lookups as scripts that return conclusions, and bring-up scripts nobody needs to read.
4. **The guard judges command text.** It blocks reads and evidence writes that mention upstream words, and lets the
   pass act unguarded. → authority by credential or effect, not by parsing.
5. **Spawning waits on the console** (§3). Of 56 waits of 10 min or more (3,585 min), 53 fell while the user was in the console and it was active (dozens of user messages, hundreds of turns inside the wait): spawns wait on a busy console, not an absent user. 51% of that wait time had all 3 slots taken (paused agents included); 49% (~1,790 min) had a free slot, 16% with no agent running at all. The console itself compacted twice on 10-31 (466k and 348k), each time losing the run's state; its growth is mostly its own output (223k of ~279k tokens in one window), and its total (~212M tokens) is ~5% of the agents'. → driving is not done by the conversational session: the pass (or a dedicated driver) spawns the moment a slot is free; paused agents should not hold a slot.
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
   (c2492318d, not upstream 31241beef); goblin-23 re-merged by hand. Confirmed: `clone <slug> <commit> main`
   resolves `main` with `git -C $SRC rev-parse main`, the shared clone's local branch, never fetched (73 commits and
   13 days behind on 10-31). 3 QA runs passed `main` (cannon-19, goblin-11, hunter-18); cannon-19 and goblin-11
   noticed and fetched the gate's scratch merge by hand. → the bring-up merges onto the gate's recorded base, never
   a local ref (R3).
10. **The hand-over asks for what the harness already knows.** 29 of 98 `hd handover` calls were refused because
   the pushed dev ref was not at the sha the agent typed. → the hand-over reads the pushed ref; it takes no sha.
11. **No agent can read the previous verdict** (`hd show` is missing; 26 failed calls), so "close every prior finding
   first" is not a step, and repeats follow. → a read command, and the checklist's first line.
12. **The shared cache download is discarded almost every run.** 36 of 49 cache steps re-downloaded the OpenRS2
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
   median ~850 s; one train rebuilt a tree identical to the previous one: liveness is commit ancestry (steps.py:75-87), never tree equality, and the pass computes all next steps from one snapshot then acts (tick.py:164), so it started a train for a head the just-written live.json already held; every rebuild makes new merge commits, so nothing noticed the same tree. A start is counted at Popen (server.py:88-95), so 7 trains that exited silently (likely the flock path) still logged a start. Integrator
   (15 runs): conflicts and gameval clashes mostly between two pinned changes, not with upstream; one wrong recorded
   resolution caused a later failure; one "conflict" was a stale MERGE_RR.lock from an overlapping train.
   → v8: a gate is keyed by tree (re-gate only when the merged tree changes); pins conflict-checked against each
   other when pinned, not at train time; one train at a time by construction.
13. **Every run builds the change twice.** The dev's own tree (`qa.sh dev`, persistent container) and a merged tree (`qa.sh gate-run`, fresh container, `clean` first) each compile and run the cache step; QA builds a third copy. → R8: one build per T, reused by dev, QA, gate and deploy.
14. **One dev-lane rebuild recompiled the whole server (cause unconfirmed).** After the clans dev added a pack module, `qa.sh dev ... :or-cache:buildCache` took 8 min 37 s: the cache build itself 15 s, then 131 `compileKotlin` tasks with 0 hits in the remote build cache, on the dev lane's 2 workers and in-process Kotlin. A plain code fix rebuilds in 15 s, so incremental compile works. The suspect, `api:generated`, was up to date in the first Gradle pass and its sources match git; the log was then overwritten by the next build (qa.sh keeps one log per step name). → keep build logs per T next to R8's build record; give the dev lane the gate's workers and Kotlin daemon.
15. **In-game testing is paced by the agent's turns, not the tools.** Across all runs the gap from a tool result to the agent's next call is a median 5.0–6.2 s (p90 ~12 s), against a median 1.2 s per tool call: 39–51% of every run's wall time is the model choosing its next step (server-dev 42%, server-qa 51%). A run costs about turns × 5 s plus builds and waits, so the lever is fewer turns per outcome (scripted flows, one call per scenario), not faster tools. UI misses ("No menu entry matching", "Widget not found") are only 3–5% of devtools calls. In a regex-matched sample of 201 actions, data-based actions failed about as often as coordinate clicks (widget_action 29%, click_menu_option 47%, interact_npc 21%, click 28%): failures come from discovering an unknown UI, not from coordinates, so the fix is known-good flows written once, not a choice of action type. A devtools call over the WSL bridge takes 0.06 s (curl.exe spawn 0.03 s, timed); one full fix iteration on the clans dev (stop, 15 s build, start, two logins) took 86 s. In 3:38-3:42 PM the dev made ~20 calls in 205 s, of which ~62 s in tools: the rest is model turns (~7 s each), plus sleeps the agent adds between steps. Logins (233 desktop.sh login calls, not chained with builds): median 37 s, p75 70 s, p90 180 s, max 558 s. The main failure is the client's devtools endpoint not answering (51 "no HTTP response": client still starting, or interop), against 12 server refusals ("login attempt refused; retrying"); each bridge call waits up to 180 s (`--max-time 180`, desktop_devtools_mcp.py:30), so a hung endpoint stalls a login for minutes. Not per-call cost. desktop.sh login clicks fixed-mode coordinates (765x503, desktop.sh:90) while the clients run resized (796x547), so centred login-screen clicks miss by ~15/22 px (likely; seen live 10-31 3:50 PM: client 2 on the login screen 3+ min with no login traffic at the server; friends-chat-11's retro saw the same for logout). Agents pipe its output through `head -c 50`, so success and failure look alike. → test flows as scripts (one call runs a whole scenario and returns the observed state; the clans dev wrote its own form.sh), a client start that blocks until the devtools endpoint answers (a fact), short call timeouts after that, a login by widget actions (no coordinates) that prints LOGGED_IN or FAILED: reason. Every code fix restarts the server (OpenRune hot-loads only external plugin jars via ::loadplugin), so each iteration re-logs in. Mirrored WSL networking (at the hand-off; a WSL restart ends every session) is for interop reliability, not speed.
16. **Shared tool side effects:** `qa.sh dev`'s cache step dirties tracked `.data/gamevals`; agents restored it by hand (24 rebuilds, ~200 min over 20 runs). → the build leaves the tree clean, checked.
   Cause: the cache step runs upstream's `mergePluginGamevals`, which by design writes all plugin gamevals into the
   tracked `.data/gamevals/*.rscm` (or-cache/build.gradle.kts:65-71, "used by release CI"): +3016 lines in 19 files
   in the clans clone. → build in a disposable copy of T, never in the tree an agent commits from.
17. **PR size drives findings, not rounds.** Diff vs base, FAIL rounds, findings: hunter 85 files +12.0k lines, 5, 34; goblin-367 9 files +1.3k, 7, 23; cannon-354 13 files +1.9k, 4, 21; genie-355 11 files +1.2k, 5, 17; friends-chat 18 files +0.9k, 2, 13. The smallest-but-one PR took the most rounds, so rounds come from the missing contract (§4.1), not size; a wide diff adds findings (hunter: data lists per feature, gameval renumbering against other branches). → a size bound helps reviewers, the checklist ends loops.
18. **The client goal's number is six days stale.** `hd` and the dashboard show `client-api: 60.9 / 100`, measured only on 10-25 (client-api/measure.json); since then 8 client changes merged to master and their commits record the probe at 90.8%, 92.2%, 92.6%, then 1168/1253 = 93.2% (client master 6cc6bbe). Only the orchestrator measures, and it ran 3 times, all on 10-25. Cause: `_measure_done` (hd/steps.py:530-536) counts the measure step as met whenever any change serving the goal is not done, and a server change is done only when upstream merges it. `server-friends-chat-clan-channels` (goal client-api, filed 10-25 20:31Z) has been open since, so the goal was never re-measured, no orchestrator ran, no client change was filed after the 10-25 backlog, and the client track has been idle since its last run (10-31 04:26Z). One slow upstream PR stops a whole track's planning. → a goal is measured whenever its target moves, and a server change unblocks the client once it is live on the test server, not when upstream merges it. The goal is re-measured by the pass whenever its track's target moves (a fact), and the number shown is that measurement with its commit (R1, R7).
19. **Half the questions to the user did not need the user.** 23 asks (~30 question texts in transcripts; answer median 5 min, p75 46 min, max 4.9 days over 10-26→10-31). Needed the user: scope and accuracy decisions (~9), upstream overlap (4), safety incidents (2). Did not: commit rewords to drop Claude-Session trailers that need a forced push the guard blocks (6, a problem the harness created), train notices that a pin was dropped (3, statements), infrastructure (3), and the same question asked 2–3 times (~6). → the harness fixes what it caused (no trailers written in the first place), notices are events not questions, an open question blocks a second ask on the same change.
20. **`hd` prints the pending step's name where a reader expects a state.** "cannon-review-354: done | merged" means "live on the test server | waiting for upstream to merge" (steps.stage, hd/steps.py:587-592), while upstream #354 is open; this monitor misread it too. → print facts ("live on test server; PR #354 open, ready, awaiting review"), not step names.
21. **The pass repeats work with no state change.** Per pass-sweep: 467 gate-pending polls (357 identical, each a
   CI API call), 202 gate records re-saved for an unchanged head, 432 identical "train running" lines, and the same
   volume repaired 68 times (gd17-dev-gradle): a repair that never converges. → act and log on edges only; a repair
   that recurs is a bug, raised once.
   Cause (hd/tick.py:103-110): a volume is an orphan when its owner label is not a running run's name, but the label
   is agent-chosen (`gd17`, `scc2`) and never equals the run name, so every live dev's volume is "orphaned" on every
   pass; `docker volume rm` is refused while the container holds it, the exit code is ignored and a repair is logged
   anyway. Harm: once a live dev's container idles out (45 min), the next pass deletes its warm Gradle home. The
   container rule (tick.py:97) has the mirror bug and almost never removes a real orphan. → every artefact is named
   after its run (no agent-chosen labels); a repair is recorded only when its effect is observed.
22. **The pass merges into a shared working tree.** Any session's uncommitted edit in ~/osrs-harness stops every
   harness merge (the monitor's draft blocked harness-dupe-check, 2026-10-31). → the pass merges in its own clone.
23. Also open in docs/ISSUES.md: a client build reached Jagex (no install-time check of the repack log); stale pins in
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
