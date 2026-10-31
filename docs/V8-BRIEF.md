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
11. **Shared tool side effects:** `qa.sh dev`'s cache step dirties tracked `.data/gamevals`, and 3 runs restored it by
   hand. → the build leaves the tree clean, checked.
12. **Wide, long-lived PRs reopen findings** (hunter: ~75 files; each feature adds data lists; gamevals renumbered
   against other branches). → a size bound per change, measured.
13. **The pass merges into a shared working tree.** Any session's uncommitted edit in ~/osrs-harness stops every
   harness merge (the monitor's draft blocked harness-dupe-check, 2026-10-31). → the pass merges in its own clone.
14. Also open in docs/ISSUES.md: a client build reached Jagex (no install-time check of the repack log); stale pins in
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
