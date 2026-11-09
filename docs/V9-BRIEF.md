# V9 brief

The hand-off for the harness developer who builds v9 on branch `v9`. It is what v8 did, measured from its own records:
`state/events.jsonl` (11,801 lines), `state/runs/*.json` (1,026 run records, 844 started), the 844 agents' transcripts
(34.7k tool calls), `harness/changes/*.md` (421 definitions), the git log of `v8` (880 commits in the window) and the
monitor sweeps `evidence/monitor/sweep-66.md` … `sweep-89.md`. Window: 2026-10-31 23:29Z (first v8 event) → 2026-11-02
22:23Z, about 47 h. Read it before docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md; ARCHITECTURE describes v8 as
built: reference, not a spec. The decided direction (docs/ISSUES.md, top entry): **one SQLite store for runtime state,
and commitments recorded, not re-derived.** The migration of the live state is actioned separately by the user.
Goal of v9: the same outcomes with fewer harness changes, fewer re-runs and a pass that costs nothing when nothing moved.

## 0. Where to start (priorities by measured impact)
Section numbers point to the evidence.
1. **The approval and the carry log** (§4.2a). The user's yes is checked against texts recomputed from the live PR,
   so a carry stopped after its push can never resume: goblin-367 was finished by hand (sweep-89 R5,
   events.jsonl:11748). #448's carry hung 83 min in its CI wait and could not be replaced (sweep-69 P1-a → sweep-75).
   2 of 12 approved carries were interrupted. → an `approval` row holds the exact texts and the ordered steps it
   covers; each carry step is a logged row; a rerun resumes from the log, never recomputes what was approved.
2. **A result belongs to the tree it checked** (§4.2b–c). Product gates ran 275 gate keys on 125 trees (2.2 per tree;
   the harness 1.0); 150 gate keys and 72 build keys re-ran an unchanged tree because a tools file or a text key moved.
   goblin-367's card was withdrawn three times on the same T (42 of the 150 min it was shown). → record each row's
   result keyed on the inputs it read (tree, the row's own code, the texts it reads), reuse it across tools ships.
3. **Typed state with migrations** (§4.1). Half the sweep findings of 66–89 trace to records with no schema: an answer
   without its question, legacy asks with no `def`, proc records with no exit status, strikes from mtimes, two `ended`
   events for one run, decisions read back from the printed status string. → one SQLite file (WAL), one table per
   record kind, foreign keys (answer → ask, verdict → run), a unique run end, a schema version and a migration per change.
4. **A pass that costs nothing when nothing moved** (§4.3). Tick CPU rose to 15–44 s per pass and 70–74 s wall against
   a 60 s timer (sweep-89 R1 P2-b); a per-pass ref cache cut it to 2.9–6.9 s, then served stale refs after a fetch
   (sweep-89 R4). → a cross-pass fact cache keyed on the refs and ETags read, invalidated by the fetch that moves them.
5. **Joins by ownership, not by mechanism label** (§4.4). 98 joins and 55 limit filings on 11-02 alone; a P0 carry fix
   joined a P1 change whose run had already started (sweep-89 R6); dependents waited on scope they never needed
   (sweeps 82, 86, 87, 88). → a filing joins only the change it names; a dependent waits on the head it needs.
6. **Harness change churn** (§4.9). 331 harness filings in 47 h, about 38% of sweep 66–89 findings regressions of an
   earlier harness ship; the harness took 55% of runs and 38% of tokens. → a replay bed: recorded state + recorded
   facts, every pass change dry-run against yesterday's real world before it ships.
7. **Questions as typed choices** (§4.5): an answer applies its effect (a dep, a kind) or it is not an answer.
8. **Hook rules and the 180 s background** (§4.7), **bring-up** (§4.6), **QA against known divergences** (§4.8).

## 0a. Before v9 starts (only the user can do these)
- The cutover state: `main` still holds v7 (docs/HANDOFF.md); v8 runs live from `~/osrs-harness` on branch `v8`. v9
  branches from `v8`.
- Remove v7's `hd-dashboard.service` (~/.config/systemd/user, `http.server 7790`): it takes a desktop devtools port
  (sweep-82 P2-b, sweep-77 P3-a).
- Decide whether agents keep the one shared GitHub token (V8-BRIEF §4.4 proposed credential authority; v8 kept the
  token and a text-parsing hook, §4.7).

## 1. Keep (the constraints, by id)
- PROBLEM axioms A1–A10, principles P1–P11; PRD R1–R8. The user's rules: CLAUDE.md "Rules" and "Shared rules", and the
  memory index `~/.claude/projects/-home-alex-osrs-harness/memory/MEMORY.md` (no deferral, ready means mergeable, one
  upstream comment per carry, card summary first, atomic not timed, limits are bugs fixed at the root).
- P2 needs one amendment for v9: "store only what cannot be derived" stays, but a **commitment** (the user's yes, a
  carry step done, a CI result of a tree, a question with its options) cannot be derived after the world moves, so it
  is stored when made. v8's bugs in §4.2 are all P2 applied to commitments.
- What worked in v8 and should carry over unchanged in behaviour:
  - spawn by path from a long-lived orchestrator (median spawn wait 0.5 min, v7 11 min);
  - events on edges (0 of 6,317 status events repeat the last one; v7 764 of 1,174);
  - the contract before code (first verdict PASS on 19 of 29 judged changes);
  - T by `git merge-tree` with deterministic commit dates, so the same T pushes the same gate sha and its green CI
    answers again (sweep-89 R3);
  - one-line hand-backs checked by the hook (verdict line, hand-over line);
  - the track scripts blocking on facts, `hd room` admission on host memory/CPU, tools run from content-hashed copies;
  - the carry over REST with one comment per head; `hd triage` of maintainer words by the orchestrator;
  - the context hand-off (46 hand-offs at the 150k limit, then the user's 800k).
- Goals: the client probe (RuneLite API methods working); the server content inventory (`server-content.json`); the
  harness's PROBLEM targets (≤5 runs per upstream change, ≤10 calls to first edit, peak context ≤200k, a due spawn
  waits one orchestrator turn) plus §3b's harness-health numbers.

## 2. What v8 is (as built)
### 2.1 The loop
- `hd.py` (3,781 lines, 272 functions, 235 KB) is the whole loop. Sections: `Facts` (git, gh, docker, process table;
  :69–586), what is stored (:606–1123), `Ctx` (the five nouns, deps, tools, T; :1124–1491), the steps and `nxt`
  (:1491–1872), `batch` (:1877), `public` (:1976), integration and the test-server deploy (:2161–2273), runs and briefs
  (:2273–2460), plan, measure, repairs, downs (:2460–2724), the pass `tick`/`_pass` (:2724–2925), the public act and
  the carry (:2925–3213), the commands (:3213–3781).
- `next(change)` (`nxt`, :1732) is the first unmet of: closed → deps live → question open → contract → hand-over at the
  dev ref → carried tools rebased → last verdict not FAIL → T (conflict, stacked) → build(T) → gate(T) → verdict → test
  server holds the head → shipped → public: carried, upstream deps, PR texts, CI, approval → carry → wait (upstream
  merge, maintainer words) → done. docs/ARCHITECTURE.md "The loop" is the full list.
- The pass `hd tick` runs from a systemd user timer every 60 s (`hd-tick.timer`) and after every run end (the hook
  starts it without waiting). It fetches each remote once, reads GitHub through `state/gh/` (ETag cache, one kept-alive
  connection), folds the hooks' fact files under the state lock, computes `nxt` for every change in priority order,
  starts script steps (build, gate, ship, deploy) in systemd scopes, ends and stops runs and processes, writes events
  on edges, rewrites `state/wake.orchestrator`.
- Commands: `hd` (pass + view), `new`, `show`, `handover`, `verdict`, `rows`, `tree`, `ask`, `answer`, `triage`,
  `hold`, `close`, `approve`, `ship`, `stop`, `scope`, `ps`, `room`, `commit`, `restart`, `tick [--dry-run]`.
### 2.2 Tracks
| Track | Base, head | build(T) | gate(T) | judge | ship |
|---|---|---|---|---|---|
| client | `origin/main`, `client/<slug>` | ninja + repack `OPENRUNE=1 LOCAL_AUTH=1`, APK `evidence/<slug>/<T>.apk` | repack log, probe, network QA | release only | batch to main; release after the yes |
| server (fork) | upstream `main`, fork `dev/<slug>` | Gradle in `build-<slug>`, image `or:<T>`, cache volume by inputs | script rows, fork CI on `gate/<slug>` at a child of T | every row | test server `or:<T_int>`; upstream after the yes |
| central | upstream main, fork `dev/<slug>` | Gradle assemble | `gradle test`, texts | every row, from `up` | live at its gate; upstream after the yes |
| filestore | upstream main, fork `dev/<slug>` | Gradle assemble (JDK 17) | `gradle test` on the live cache | every row | upstream after the yes |
| harness | live branch (`v8`), `harness/<slug>` (+ `harness/<slug>` in each product repo whose tools it changes) | the suite at T | tests, `hd tick --dry-run` vs live, each carried tools head's tests | none | batch fast-forward under `state/ship.lock` |

Each product track's scripts sit on its repo's tools branch (hd.yaml: `client/harness-v8`, `local/harness`), worktree
`<repo>/.worktrees/<branch tail>`: `tools/track.sh build|up|down|gate|ship|measure|log|test`, `tools/build/build.sh`,
`tools/gate/gate.sh`, `tools/server/*` (the fork's ~2.8k lines). A track script copies its `tools/` to
`state/tools/<hash>/tools` and execs there, so a ship never moves a running step.
### 2.3 T, T_int, keys
- T = `git merge-tree --write-tree` of base + the closure of deps' heads (`Ctx.deps`) + head, committed with
  `commit-tree`, dated the newest parent's date. With Central deps, `-c<central12>` is appended (Central tree built in).
- T_int = the same over every gated open server head + the 45 permanent `pins` (hd.yaml), deployed as `or:<T_int>`; a
  conflict lists the later-merged change's dev; `local/merge/<a>-<b>` refs record resolutions.
- Build key = T's tree + `-<hash12>` of `tools/build/*`. Gate key = build key + hash of `tools/gate/*` (only the part a
  row's verb reaches, `hd.gate_part`) + each tools file a row names + contract script rows + (public tracks) the texts'
  hash. Row key = the same over one row (`ROWKEYS`); `state/<slug>/row-<kind>-<id>.json` keeps the last four keys.
- Deploy key = T_int's tree + hash of `tools/track.sh`, `tools/build/`, `tools/server/`.
### 2.4 Judgments, carry, triage
- `hd handover` (dev) runs every `check:` row, records `{head, T, tools, given, limits, at}`; refuses on a conflict, a
  failing row, an empty evidence dir, a prose limit. It prints the one hand-back line.
- `hd verdict <slug> <head> <rows.json>` (qa) appends `{head, contract, judged, rows, rules, run}`.
- The card: each act the carry does and each exact text; the user types `! hd approve <slug> <head>` →
  `approval.json {head, texts: digest}`. `hd ship` (started by the pass) re-checks `approved()` (hd.py:2065), which
  compares the digest against `public_texts(ctx, ch)` (hd.py:2994): texts recomputed from the **live** PR (title/body
  only if they differ from the live ones, push summary only if the push still moves the PR).
- The carry (hd.py:3155): push (no force), open draft or PATCH title/body, CI green at head, one comment naming the
  head and quoting every finding, ready; each step a `ship.log` line; `ship.json {head, ok, fault, detail}`.
- Maintainer words: the pass lists each untriaged one; the orchestrator runs `hd triage <id> finding|ask|ack`
  (`state/triage/<id>.json {verdict, ts}`); a finding joins the PR's one open round or files `<track>-<pr>-c<id>`.
### 2.5 The hook (`hook.py`, 727 lines)
SubagentStart/Stop bind and end runs (fact files, never the state lock); SessionStart rereads the orchestrator's
definition; PostToolUse ends a run on the orchestrator's TaskStop and enforces the context limit; PreToolUse rules:
`hd approve`/`close` only by the user; no acting `hd` pass in a subagent; `hd scope <run>` prepended to every run's
Bash command (systemd slice per run); hand-back held while background tasks run; hand-back must be the recorded line;
reader write rules; kill only own slice/jobs; self-matching `pgrep -f` waits; `timeout` and counting sleep loops
denied; desktop devtools calls limited to the run's ports; idle-desktop `down` notice.
### 2.6 Roles
`.claude/agents/`: orchestrator (72 lines; the driver and the user's chat: watch on `state/wake.orchestrator`, `hd`,
spawn by path, TaskStop at hand-back, cards, questions, triage, files harness changes, keeps one monitor sweep
running), dev (56), qa (55; contract mode writes the contract before code, judge mode the verdict), planner (28; goals
and operations: merges harness changes per mechanism with `--supersedes`), reader (20; a run's read-only lookup). The
agent count is 7 (hd.yaml `agents`), the hold band `P2`.
### 2.7 Where the state lives (v9 replaces exactly this)
All under `~/osrs-harness/state/` (git-ignored, 3.7 GB, mostly logs and per-change postgres dirs), written by
temp-file + rename (`hd.write`), no schema, no version, no transaction across files.

| Path | Writer | Shape | Count now |
|---|---|---|---|
| `events.jsonl` | hd, hook (via fact fold) | one JSON line; **no type field**: the kind is which keys are present (below) | 11,801 |
| `runs/<run>.json` | hd (fold) | `{name, role, mode, change, step, input, brief, given, deps, listed, started, started_at, ended, reason, record, last, usage{turns,input,output,cache_read,cache_creation}, agent_id, transcript, console_pid, console_start, folded[], handoff_told}` | 1,026 |
| `runs/by-agent/<agent_id>` (+ `.idle`) | hook | the run name; the desktop idle call count | 843 + 73 |
| `facts/<ns>-<pid>.json` | hook | `{fact: bind\|resumed\|end\|stopped\|told\|context-limit, run, …}`; id from the wall clock (`01793657259026346875-2811611`), deleted when folded | 0 now |
| `briefs/<run>.md` | hd | the run's prompt (definition, contract, last verdict, build/gate lines, hand-off) | 1,031 |
| `<slug>/handover.json` | `hd handover` | `{head, T, commit, tools{repo: head}, given, limits, at, ts}` | 346 |
| `<slug>/verdicts.jsonl` | `hd verdict` | `{head, contract, judged, rows{id: pass\|fail: note\|not-judged}, rules{file: blob}, run}` appended | 29 |
| `<slug>/build.json`, `gate.json` | track scripts | `{T: key, ok, detail, head}` | 236, 209 |
| `<slug>/row-<kind>-<id>.json` | `hd rows` | `{keys: {rowkey: {out, rc, ts}} (last 4), ts}` | ~500 |
| `<slug>/proc-<build\|gate\|ship>.json` | hd (`Ctx.start`) | `{pid, start, args, key, rows, attempts, since, cause, rc, result, room, script, ts}` | 585 |
| `<slug>/<script>.rc` | spawn wrapper | exit status; absent = killed | — |
| `<slug>/ask.json` | `hd ask` | `{text, def, ts}` (def: hash of kind, deps, pr; legacy ones lack it) | open asks only |
| `<slug>/hold.json`, `approval.json`, `ship.json`, `opened.json`, `reopened.json` | hold, approve, ship | `{head, held}`, `{head, texts, ts}`, `{head, ok, fault, detail, ts}`, `{pr, head}`, `{head, checks}` | few |
| `<slug>/state.json` | the pass | `{state: "<printed status>", ts}`; **read back as input** (hd.py:2408 `startswith(("done","closed"))`, :2709 regex for a deploy conflict, :3610 `startswith("carried")`) | 423 |
| `<slug>/swept.json` | the pass | `{head, ts}`: the dev ref's head when its branches were removed | 375 |
| `<slug>/tools-conflict-<repo>.json`, `repair-<name>.json` | the pass | `{head, onto, detail}`, `{attempts}` | few |
| `<slug>/up.json` | track `up` | `{started, script, repo, containers, modulus, accounts, admins, token}` | live stacks |
| `<slug>/build.lock`, `desktops.lock`, logs (`build-<key>.log`, `gate.log`, `ship.log`, `desktopN.log`, `keep-N.log`, `tests.txt`), `spotless.git`/`test.git` (row worktrees), `key/`, `game.yml`, `postgres/` | scripts | files | — |
| `<goal>/measure.json` | track `measure` | `{tree, value, report}` | — |
| `live/tree.json` | live deploy | `{tree, commit, heads[], names, modulus, key, containers}` | 1 |
| `ship-harness/gate-<key>.json`, `shipped`, `tests.txt` | harness batch | per-prefix gate records | — |
| `integration/build.json` | live build | `{T, ok, detail}` | 1 |
| `triage/<comment id>.json` | `hd triage` | `{verdict, ts}` | 38 |
| `gh/<hash>.json`, `gh/quota.json` | Facts | `{url, code, etag, body, next}`, `{reset, at, url}` | 38 |
| `fetch/<hash>` | Facts | last fetch result of a clone, flocked | 9 |
| `room/<pid>.json`, `room.lock` | `hd room` | `{pid, start, mem, cpus, owner, held}` | live |
| `winpids/<slice>/<pid>`, `tmp/<slice>/` | scripts, `hd scope` | Windows process image; a run's TMPDIR | live |
| `seen.orchestrator.json`, `wake.orchestrator` | `wake()` | `{spawn[], card heads{}, …}`; the new lines | 1, 1 |
| `orchestrator-read/<pid>-<start>`, `orchestrator-started`, `orchestrator-restarting`, `orchestrator-handoff.md`, `stopped` | hd, hook, the session | blob held; flags; the session's unrecorded words (questions asked in text, cards shown) | — |
| `ship.lock`, `.lock` (the state lock) | hd | flocks | — |
| `client-live.lock`, `desktop.lock`, `emulator-port.lock` | track scripts | flocks | — |
| `main-told`, `seen.main.json`, `wake.main`, `inbox.jsonl`, `inbox.read`, `allow-relay.log`, `quest-*`, `hunter-feat-pr/` (v7 names) | nothing in hd.py or hook.py | v7 leftovers | cut |

**events.jsonl shapes** (key set → count): status `{change, state, detail}` 6,316; run lifecycle `{action: listed|started|ended|processes-ended|relisted|resumed, change, run, role?, reason?, record?, turns?, tokens?}` 1,044 / 846 / 888 / 361 / 9 / 25; records `{change, record: handover|answer|verdict|closed|ask|superseded|approval|hold|message|decline|triage, head?|text?|failed?|by?}` (523 hand-overs, 148 answers, 66 verdicts, 46 closed, 39 asks, 12 approvals); filings `{action: new|joined|limit|dep, change, by?, slice?, track?, dep?}` 390 / 98 / 55 / 74; hook `{action: denied|idle-refused|desktops-idle|context-limit|handback-held|stop-unmatched|nested-stopped|spawn-refused, agent?, rule?, run?, tasks?}` 122 / 55 / 56 / 46 / 19 / 11 / 6 / 4; pass processes `{action: "stopped gate"|"stopped build"|"stopped ship", change, key, pid}` 33 / 18 / 14; `closed branches` 378; `rebased tools` 12. Rotated at 20 MB. The v7 monitor scripts (`evidence/monitor/kpi.py`, `phases.py`, `tick.py`) read a `kind` field and `harness/state/`: they do not run on v8's events.

**contract.md** (`evidence/<slug>/contract.md`): a header `rules: AGENTS.md=<blob> .github/CONTRIBUTING.md=<blob> .github/pull_request_template.md=<blob>`, `agreed: <run>`, then rows `- <id> | <text> | check: <cmd> | judge: <kind> [| upstream]` (`check:` a script row run at hand-over and gate, `gate:` a gate-only row, `judge:` a qa row; `| upstream` seeds only a change that opens a PR). Answer rows `- answer-<n> | <ts> the user[, to "<question>"]: <text> | judge: <kind> [| holds: <a,b>]`; joined filings `- answer-<n> | filed by <filer>: … | holds: …`; findings `- answer-<n> | finding <id> by <author>`. The kind of an answer row is read from its text prefix.

**harness/changes/<slug>.md** front matter (key → count of 421): slug, track, title, kind (change|release|local), priority (P0–P4), deps, created (all); mechanism 158; closed 47; goal 44; superseded 30; units 26; limit-of 25; pr 20; finding 19; branch 19; held 5; network 5; quest-mode 2; folded 1; reopen 1. Body = the scope, joined filings appended as text. Definitions stay files in v9 (git history; agents and the user edit them as text), as do evidence and PR texts.

## 3. Numbers v9 must beat
### 3a. Comparable to V8-BRIEF §3
v7: 2026-10-25 → 10-31, 132 runs (V8-BRIEF). v8: the window above, from events.jsonl, runs/*.json and transcripts.
Run kinds by the definition's track and kind; tokens = input + output + cache read + cache creation.

| Metric | v7 | v8 (measured) | v9 target |
|---|---|---|---|
| runs per upstream PR | 15–23 | #354 36, #367 34, #408 30, #355 24 in 47 h (server runs grouped by `pr` / slug number); 24 server changes with no PR yet took 169 runs | ≤10 per PR round |
| runs per upstream change (median) | 15 | 5 (42 changes; 283 runs, 92.5 agent-h, 2.29B tokens) | ≤5 (PROBLEM) |
| what triggered runs | QA FAIL/check ~36, question ~30, gate/train ~23 of 95 | server-upstream 283: review due 78, a successor after a run ended without hand-over 49, contract 36, dev due 30, gate failed 18, FAIL rows 13, reply 10, answer 8, build failed 6, joined filing 4, comment misses findings 2. Harness 461: dev due 328, tree conflict 33, a filing joined after the hand-over 27, gate failed 25, successor 22, answer 16 | successors and harness-made re-runs (tree conflict, rejoins, re-gates) → 0 |
| per change by kind (median runs / agent-h / tokens) | upstream server 15 / 5.4 h / 290M; client 2 / 1.0 h / 56M; local server 3 / 0.8 h; harness 1 / 0.3 h | upstream server 5 / 1.3 h / 32M (42); central 5.5 / 1.0 h / 20M (2); client 2.5 / 1.0 h / 8M (6); local server 9.5 / 3.3 h / 44M (2); harness 1 / 0.11 h / 2.6M (325) | upstream ≤5 / ≤1 h |
| per run (median) | — | dev 6 min, 35 turns, 2.2M tok (643); qa judge 23 min, 63 turns, 5.4M (92); qa contract 6 min, 2.6M (60); planner 2 min (30); orchestrator runs 2 min (19) | — |
| QA rounds per PR | up to 9 (goblin 4,2,1,PASS,4,6,4,2) | #408 hunter 10 verdicts, none PASS (fail rows 1, 42, 9, 11, 4, 6, 4, 10, 7, 8); all others 1–3; first verdict PASS on 19 of 29 judged changes | ≤3, findings falling each round |
| spawn wait after the record that makes a run due | median 11 min, p90 83, max 534 | listed → started: median 0.5 min, p90 1.8, max 416 (844 runs) | keep |
| context (start / peak median / max) | ~35k; server-dev 160k, server-qa 189k, client-dev 207k; max 887k | ~36k; server-dev 84k (p90 157k), qa judge 125k (p90 196k), qa contract 93k, client-dev 83k, harness-dev 73k; max 965k (a qa contract run) | peak ≤200k at p90 |
| tool calls before first edit (median) | server-dev 81, client-dev 52, server-qa 148 | server-dev 15, client-dev 14.5, harness-dev 11, qa judge 28.5 (first write). Method: first Edit/Write or Bash write (`sed -i`, `cat >`, heredoc to a file, `.write(`, `tee`); v7's exact method is not recorded, so compare with care | ≤10 |
| share of calls that are sleep/until polling | 12% | 7.3% of 34.7k (Bash or Monitor naming sleep/until/while); client-dev 14.1%, server qa 8.0%, server dev 7.9% | ≤3% |
| guard denials, wrong | ≥ half of 44 | 122 (113 on 11-02); ≥7 judged wrong by sweeps (reader git/quote/gh-api rules 4, kill of an own job and `kill -0` 2, a counter misread 1); time bound 40 and kill 11 judged right | 0 wrong |
| step events repeating the last | 764 of 1,174 | 0 of 6,317 | keep |
| model time share per run | 39–51% | not measured | — |
| asks (count; answer median, p75, max) | 23; 5 min, 46, 4.9 days | 39 (server 20, harness 15, client 3); 6 min, 19, 315 min | needed ones only |
| context hand-offs | none | 46 at the 150k limit (11-01 00:30–15:04Z), then the limit raised to 800k | — |

### 3b. Harness health (new; v9 tracks these)
| Metric | v7 | v8 (measured) | v9 target |
|---|---|---|---|
| harness changes filed per day | 2 with runs in 6 days | 200 on 11-01, 122 on 11-02 to 22:23Z (`new` events, track harness: 331); plus 98 joins and 55 limit filings on 11-02 | <20/day, falling |
| share that were regressions of a previous harness ship | — | ~25 of ~66 findings in sweeps 66–89 (38%) name a shipped harness commit as the cause or a fix that did not hold (by hand from the sweep text; list in §4.9) | <10% |
| filing → first ship of a harness change | — | median 14 min, p75 28, p90 50 (189 changes with a `new` event and a `T:` commit) | keep |
| harness changes shipped more than once | — | 20 of 221 shipped slugs have >1 `T:` commit (`harness-stop-hook-subagent-wording` 5) | ~0 |
| harness share of agent effort | 2 runs | 461 of 844 runs (55%), 65.8 of 174.9 agent-h (38%), 1.57B of 4.14B tokens (38%) | <15% |
| churn of the loop | — | in the window: hd.py 290 commits, hook.py 60, tests 389, ARCHITECTURE.md 405, PRD.md 212 | — |
| tick CPU / wall per pass | median <1 s, max 14 s (v7 journal) | journal 19–22Z: CPU median 6.7, 8.8, 8.9, 4.3 s per hour, max 44.4 s; wall 70–74 s against the 60 s timer at the peak (sweep-89 R1); 2.9–6.9 s CPU after 29a7876 | CPU <1 s when no fact moved; wall < timer always |
| builds / gates per tree | ~7 builds per round | 650 build keys on 578 trees (1.12); product gates 275 keys on 125 trees (2.2), harness 1.0 | 1.0 / 1.0 |
| cards withdrawn by a re-gate on the same tree | — | 5 (goblin-367 3, 42 min of 150; central-token-login-op 1; quest-cooksassistant 1) | 0 |
| carries interrupted | — | 2 of 12 approvals (#448 hung 83 min in its CI wait; goblin-367 stopped after push, unresumable, finished by hand); live deploys stopped on a moved key 12 | 0 |
| runs started with nothing to do | 2 empty | 120 of 844 started runs ended without their own record (14%): stopped by the head 41, no record 21, waits (batch, dep, question) 17, step moved 15, console died 7, change done/closed 6; plus 182 of 1,026 listed runs dropped unspawned | <5% |
| runs with two `ended` events | — | 22 of 859 (fixed by bab772d) | 0 by constraint |
| tool results backgrounded at 180 s | — | 653 in run transcripts | waits by notification only |
| build artifacts retained after their change closed (docs/V9-RETENTION.md) | — | all: 830 images (242 GB), 58 per-slug Gradle volumes (65 GB), 157 QA clones (110 GB), 29 contexts (16 GB), 54 GB build cache, none released (2026-11-06) | 0 images, volumes, clones, worktrees per closed change (`hd kpi`: artifacts of closed changes) |
| images on the host | — | 830 | those of open changes' heads and staging (`hd kpi`: images recorded) |
| free space on the host drive over a 47 h window | — | C: 94% full (868 of 931 GB) | end = start, within the open changes' artifacts (`hd kpi`: free space) |

Not measured: model time per turn, PreToolUse hook latency, how many of the 39 asks needed the user, a per-change life
split like V8-BRIEF §2 (phases.py does not parse v8 events). A v9 store should make each of these one query.

### 3c. The upstream outcome in the window
Carried ready: #355 (306d7edcd), #445 (07f01dc9a, merged 16:34Z), #448 (8c6d9679e), #367 (def7f2c59, by hand after
the interrupted carry); one carry fault (a 404 on a reply, cannon #354 round, 07:35Z). Hunter #408: 10 FAIL rounds,
not carried.

## 4. What failed, and why (the root causes)
Each item: the root cause, the evidence (sweep and events.jsonl lines), and whether v9's direction (SQLite store,
recorded commitments) fixes it or it needs other design.

### 4.1 Untyped file state (fixed by the store)
- **Legacy records lacking new fields.** Asks written before `def` existed are open forever (`asked()` hd.py:787-790):
  three questions stayed open after their definitions became exactly what they proposed (sweep-83 P2-a). answer-5
  without `holds:` could not hold `client-login-segv-osclient`, which ran twice more (sweep-88 P1-a, sweep-89 R1 P3-a,
  R2 P2-a; events.jsonl:10851-10852, 11598-11600, 11638-11639; fixed by hand-editing the contract). Proc records
  written before `rc` counted as deaths; the orchestrator deleted `state/ship-harness/proc-ship.json` twice by hand
  (sweep-70 P0-a, sweep-71). Contract rows seeded under kind `change` stayed after the kind became `local`
  (sweep-80 P2-a). → a schema version, a migration per change, NOT NULL columns with defaults.
- **Text-prefix classification.** `late_answers` classed the user's quoting answers as joined filings by
  `startswith("the user:")` for 10 min (sweep-88 P2-a); the kind of every answer row is its text. The printed status
  is read back: `state.json` decides done/closed (hd.py:2408), a deploy's blocker (:2709) and carried (:3610).
  `cause()` reduces each log line to a "cause" by dropping hashes, so every successful ship read "v8 at" and counted
  as three same-cause deaths (sweep-69 P0-a). → typed columns (`answer.kind`, `run.end_reason`, `step.code`).
- **Answers without their question.** `add_answer` writes `the user: a` and drops `ask.json`
  (evidence/server-token-refusal-logged/contract.md answer-1); the user's (a) = "add dep server-token-auth" was never
  applied, run -2 built without it and filed a needless harness change (sweep-85 P2-a, events.jsonl:11458-11459). The
  #448 round went to a server-track run with a bare "the user: a" (sweep-89 R3, :11701-11703). → `answer.ask_id`
  foreign key; the options stored with the ask.
- **Strikes from file presence and mtime.** `start()` resets its 3-strike count only on a newer `ship.json` (never
  written by ship-harness) or a newer script mtime (sweep-69 P0-a, sweep-70 P0-a, sweep-72); a new key resets it, so a
  key-independent fault never converges (sweep-66 P1-b: 19 recreated, 30 failed live ships); a flaky test on the mtime
  (`harness-attempts-test-mtime-flake`, sweep-87); an identical failed record on rerun counts a strike (sweep-88 P4-a).
  → `attempt` rows (process, key, exit status, cause code), a strike is a query.
- **Wall-clock ids.** Fact ids are `<time>-<pid>`; the fold had to stop ordering by id because the clock steps back
  (ARCHITECTURE "state/facts"; fix 0645954, sweep-71). → INTEGER PRIMARY KEY.
- **Double `ended` events.** The hook's end fact and the pass's settle both end a run; the fold dropped the hand-back's
  usage (sweep-84 P4-a; 22 of 859 runs; events.jsonl:11366-11367). → one `run.ended` column, set once in a transaction.
- **Events with no type.** An event's kind is the set of keys present; a denial event lost its verb to a `[:60]` cut
  (sweep-71 P5-a) and carried no run (sweep-76 P5-a). → an `event` table with a `kind` column.

### 4.2 Decisions re-derived from live facts (fixed by recording commitments)
- **a. The approval.** `approved()` (hd.py:2065) compares `approval.json`'s digest with `public_texts()` recomputed
  from the live PR (:2994). After the carry pushed and edited the body, the live PR changed, so the recomputed texts
  dropped the title/body acts and the digest no longer matched: the rerun refused "no yes at def7f2c59 and these
  texts" (ship.log 22:04:13-14Z; stop events.jsonl:11748; sweep-89 R5 P0-a). A harness ship (eee436a) restarted the
  carry because a carry alive on a changed hd.py is restarted by design (ARCHITECTURE "The pass"). The #448 carry
  hung in its CI wait because `F.ci` returned an old failed run beside the new success (sweep-69 P1-a), and the
  outdated-carry branch was unreachable (sweep-73 P1-a) until 6fbe9b5 (sweep-75). → the approval row holds the
  ordered step list and exact texts; each step's done-ness is a logged row; resume = the first step not logged done.
- **b. Gate keys on tools helpers.** A behaviour-free tools edit (`grep -q` → `grep -x >/dev/null` in gate.sh) moved
  the gate-ci key and re-ran fork CI on four unchanged trees (sweep-85 P3-a, events.jsonl:11347-11353); 79b12fedc
  rebuilt every server change on a new tools key and triggered a live redeploy that hung (sweep-67). The texts key
  re-ran spotless and every row, not just text rows (sweep-80 P4-a, :11132-11147). → a CI result row keyed on
  (tree, workflow files); a row result keyed on what the row read.
- **c. Whole-tree re-gates on every tools ship withdraw cards.** f288293 re-gated every server card once on unchanged
  trees (sweep-89 R1 P4-a); goblin-367 lost its card 20:12-20:15, 20:50-21:09, 21:40-22:00 on tree 6140b42e3 (§3b).
- **d. Other re-derivations met:** T_int dropped a change whenever its base or a dep moved until its re-gate, so the
  live server flipped with and without it (sweep-67 P3-b); a merged PR found only through `opened.json`, so #445
  showed a new draft card after merging (sweep-66 P2-b, sweep-81); a change's tools set read from the live hd.yaml,
  so a change adding a repo never gated its tools commit (sweep-89 R1 P2-a); dependencies defined twice (`Ctx.deps`
  vs raw `deps`, sweep-86 P4-a); a hand-off file's mtime as run input, so a "blocked on a dep" hand-off relisted the
  run 3 s later (sweep-89 R2 P2-a); "head not handed over" written while the run was live (sweep-67 P5); a deploy
  that never restarted the container waited forever on a ready line (sweep-67 P0-a).

### 4.3 Pass cost (store + a cross-pass fact cache)
Every pass re-reads every git and GitHub fact: one pass ran 116 `gh api` and 91 `merge-base --is-ancestor` (71 in the
harness repo, one per harness change of 331 definitions); CPU 15–44 s, wall 70–74 s against a 60 s timer (sweep-89
R1 P2-b); cost scales with gates in flight (R2 P5-a); each new key digest raised it (sweep-86 P4-a 7-8 → 8.6-9.6 s;
sweep-88 P5-a 9.9-10.3 s). 3781b48 read all refs once per pass; `Facts.fetch` did not forget the map, so a pushed dev
ref looked unhanded-over and a stale base skewed T (sweep-89 R4 P1-a, joined into harness-tick-cost-cache); fake
Facts hid it from tests. The pass also prints the waiting card each time (830 KB of journal in 29 min, ~40 MB/day;
sweep-87 P5-a). → a fact table keyed on (repo, ref) and (url, etag) across passes, invalidated by the fetch that
moved it; done changes leave the per-pass scan; the pass acts on changed facts only. Needs design beyond storage: an
index from a fact to the changes that read it.

### 4.4 "One open change per mechanism" joins unrelated work (other design)
`hd new` joins a filing to the open change on its mechanism label. The label is not code ownership: two changes edited
`deps_held` in parallel (sweep-87 P4-a); a limit target soaked up an unrelated join before its first hand-over, so
filestore waited on scope it never needed (sweep-87 P2-a, :11549-11560); a limit joined a change itself blocked down a
chain of five (`harness-desktop-one-login-path`, 8 joined filings none startable; sweep-82 P2-a, :11252-11256); a
dependency reopened by an unrelated join kept its dependents waiting (sweep-86 P2-a); the P0 carry fix joined a P1
change whose run started before the join, so it lands after that scope (sweep-89 R6 P3-a); joined filings stopped
holding dependents, then held the wrong ones (sweep-88 P1-a). Volume: 98 joins and 55 limit filings on 11-02. A round
that must move repos (#448 → OpenRune-FileStore) had no step (sweep-75 P2-a, sweep-89 R3). → a filing is its own
change unless it names the change it extends; a dependent waits on the head it named; merging is the planner's
explicit act. The store helps (a `join` row with who holds whom) but the rule is design.

### 4.5 Questions and answers (store for the link; design for the effect)
39 asks in 47 h. An answer did not apply its option (§4.1); a question cleared only through `hd answer`, so a
definition commit that answered it left it open (sweep-80 P2-a); `settled()` hashed every front-matter key, so a
harness write could settle the user's question (sweep-83 P3-a); `hd new` accepted deps `[]` for code living on
another change's branch, and the contract qa had to ask the user (sweep-76 P3-a, sweep-79). The orchestrator keeps
questions asked in text in `state/orchestrator-handoff.md`, outside every record. → an ask row with typed options,
each option an effect (dep, kind, waive, close, move repo); the answer is the chosen option id; the effect is applied
in the same transaction.

### 4.6 Desktop and mobile bring-up (other design)
The live stack: a WSL restart left a file bind mount stale and every live ship failed (sweep-66 P1-a); a deploy that
did not recreate the game container hung in `ready` and blocked every later deploy (sweep-67 P0-a); a stopped ship
leaked a 1.3 GiB boot container (sweep-69 P2-a). Issuer login: the token-login chain held six changes (client-devtools-login →
harness-mobile-up-by-facts → client-login-segv-osclient → harness-live-stack-issuer → relogin-js5, token-refusal;
sweep-82 P2-a). Port conflicts: desktop 11 could not bind 7790, held by v7's dashboard unit (sweep-77 P3-a,
sweep-82 P2-b). APK cache: `unzip -p | grep -q` under pipefail returned 141, so every up rebuilt the live APK under
`client-live.lock` (sweep-79 P1-a); the same SIGPIPE pattern sits latent in the server `ready` and `down` (sweep-80
P5-a). walk_to ran 30 min silent and ignored the cancel (sweep-76 P2-a). Agents drove desktops over raw HTTP with
another change's token, past the hook (sweep-77 P5-a). → bring-up stays scripts on the tools branches; each is a
state machine whose steps are logged rows, so an interrupted up resumes and a hung one names its step.

### 4.7 Hook rules (other design)
The hook judges command text: reader rules denied read-only `git merge-base`, `stash list`, `config --get`
(sweep-67 P3-a, :18:05:41Z), a grep with an apostrophe inside double quotes (sweep-68 P3-a, :10627), `gh api -X GET`;
the kill rule denied `kill $p` after `& p=$!` (sweep-77 P4-a, :11081) and `kill -0` (sweep-82 P4, :11239); a counter
was misread in an until-wait (sweep-89 R3 P5-a). Claude Code backgrounds a subagent's foreground command at 180 s
(653 results), while dev.md/qa.md/hook text said 600 s (sweep-83 P4); the next fix told runs to wait on the
notification while `end_run` refused a turn end with a background command running (sweep-84 P3-a). → fewer rules:
the two that guard the user's authority (`approve`, `close`) and the run's own processes by slice, not by text;
roles written for the 180 s background as the normal case.

### 4.8 QA passing known divergences (contract design)
qa16 accepted a dev's "test-only, accepted" divergence list the user never accepted and marked a row pass unchecked
(sweep-79 P2-a, :10071); the local test row ran `<module>:test` only while upstream CI runs integration tests, a
13-minute round trip to learn it (sweep-78 P2-a); the fix then ran a task 14 modules do not register (sweep-84 P2-a).
Hunter #408: 10 FAIL rounds (§3a). → an `accepted_difference` row only the user's answer creates; local rows that are
the upstream CI's task list read from its workflow.

### 4.9 The harness-fix churn rate (store + a replay bed)
Monitor sweeps found a regression in almost every harness ship. In sweeps 66–89, about 25 of ~66 findings name a
shipped harness commit as the cause: reader rules (67 P3-a, 68 P3-a), strikes on successful ships (69 P0-a, 71 P1-a),
an unreachable outdated-carry branch (73 P1-a), stale docs after a roles fix (75 P5-a), the APK SIGPIPE (79 P1-a,
from 53b837c), the texts key re-running all rows (80 P4-a, 7f1aaa9), a flaky spawn test (81 P2-a), `kill -0` (82 P4,
534fd05), legacy asks and `settled()` (83 P2-a, P3-a, 8242da4), the integration task (84 P2-a, dd863ba52), roles vs
hook (84 P3-a, d297d90), a slice test (85 P5-a), `Ctx.deps` (86 P4-a, 60891e9), the holds rewrite (88 P1-a, 2c15195),
quoting answers classed as filings (88 P2-a, d4f21fe), new-ok strikes and tick CPU (88 P4-a, P5-a), tick CPU and the
holds field (89 R1 P2-b, P3-a), the tools-ship re-gate (89 R1 P4-a, f288293), the stale ref map (89 R4, 3781b48), the
carry stopped by a ship (89 R5, eee436a). Causes: each fix is tested against fakes (`tests/test_hd.py`, 5,123 lines,
over fake git/gh/docker) and shipped within a median 14 min; old records meet new code with no migration; one
mechanism patched by several changes in parallel. → v9: the store makes a real day replayable (snapshot the DB, replay
the fact log through a candidate pass, diff the decisions) and a schema migration is code with a test; the gate's
check-dry-run runs against that snapshot, not fakes.

### 4.10 Which v9's direction fixes
| Root cause | SQLite store + recorded commitments | Needs other design |
|---|---|---|
| 4.1 untyped state | fixed: schema, FKs, unique ends, migrations, typed kinds | — |
| 4.2 re-derived decisions | fixed for approval/carry, CI per tree, row results per input, tools set at head | T_int membership rule |
| 4.3 pass cost | the cross-pass fact cache | an index from fact to readers; event-driven passes |
| 4.4 joins | records who holds whom | drop mechanism-label joins |
| 4.5 questions | ask ↔ answer link | options as effects |
| 4.6 bring-up | resumable step logs | scripts, ports, the live stack |
| 4.7 hook | — | fewer text rules; 180 s as normal |
| 4.8 QA divergences | accepted-difference rows | local rows = upstream CI tasks |
| 4.9 churn | replayable snapshots, migrations | ship only what replays clean |

## 5. Component ledger: cut, merge, keep
Lines now; churn = commits in the window. Rules as in V8-BRIEF §5: unused and no R needs it → cut; several doing one
job → merge; patched often → rewrite, don't port.

| Component | Lines | v8 churn / use | Verdict |
|---|---|---|---|
| `hd.py` stored records (:606–1123: contract, asks, verdicts, facts, fold, events, wake) | ~520 | most of §4.1 | rewrite on SQLite: one module of tables and queries; keep `hd.write`'s atomicity as transactions |
| `hd.py` `Facts` (:69–586) | ~520 | the pass's reads | keep the reads; add the cross-pass cache table |
| `hd.py` `Ctx` + `nxt` + steps (:1124–1872) | ~750 | 290 commits on hd.py | keep `nxt`'s order; deps one definition; inputs from stored rows, not file mtimes or status text |
| `hd.py` carry and public act (:2925–3213) | ~290 | the P0 | rewrite as a logged step list bound to the approval row |
| `hd.py` batch, integration, ship_test (:1877–2273) | ~400 | live deploy findings | keep; deploy steps logged |
| `hd.py` runs, briefs, settle, unlistable (:2273–2460) | ~190 | double ends, relists | merge into a `run` table with one end |
| `hd.py` `cmd_new` + joins (:3557–3706) | ~150 | §4.4 | cut mechanism joins; keep `--blocks`, `--limit-of`, `--supersedes` as explicit edges |
| `state.json`, `swept.json` | — | read back as text | cut: derive from the store |
| `proc-*.json` + `<script>.rc` + `repair-*.json` | — | strikes | merge into `process` and `attempt` tables |
| `row-*.json`, `build.json`, `gate.json`, `ship-harness/gate-*.json` | — | re-gates | merge into `result` keyed on inputs |
| `facts/`, `events.jsonl`, `runs/` | — | hook ↔ pass | merge into `fact`, `event`, `run` tables (WAL: the hook writes directly) |
| `seen.orchestrator.json`, `wake.orchestrator`, `orchestrator-handoff.md`, `orchestrator-read/` | — | the session's memory | the view's seen marks and the session's open questions as rows; the wake file stays a file for inotify |
| v7 leftovers in `state/` (`main-told`, `seen.main.json`, `wake.main`, `inbox.*`, `allow-relay.log`, `quest-*`, `hunter-feat-pr/`) | — | read by nothing | cut |
| `hook.py` | 727 | 60 commits; 122 denials, ≥7 wrong | keep bind/end/hand-back/context; cut text rules beyond approve/close and own-slice kills |
| `tests/test_hd.py` | 5,123 | 389 commits | keep one class per R; add replay tests over a recorded DB |
| track scripts (`tools/track.sh` ×4, fork tools ~2.8k lines) | — | bring-up findings | keep; steps logged; no `\| grep -q` under pipefail |
| roles (`.claude/agents/*.md`) | 231 | 64 commits | keep; one wait rule for the 180 s background |
| `docs/ARCHITECTURE.md` | 614 (75 KB) | 405 commits | rewrite for v9 at one page per mechanism; the state section becomes the schema |
| `evidence/monitor/*.py` | — | read v7's `kind` events | rewrite as queries on the store, so §3's numbers are one command |
| definitions, evidence, PR texts | — | edited as text by agents and the user | stay files (ISSUES) |
| contract.md rows | — | qa writes them as text; the pass classifies answer rows by prefix | move to the store (ISSUES) with typed kinds and `holds`; qa writes rows through `hd`, `hd show` prints them |
