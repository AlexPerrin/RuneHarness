# Architecture of the harness (hd)

The solution to docs/PROBLEM.md that meets docs/PRD.md (R1–R8). One loop over five nouns: a **change** (definition and
contract), its **tree** T, the **judgments** bound to T or to the head, its **targets**, and the **runs** that worked
it. `next(change)` is the first unmet of a fixed list; everything shown or acted on is read off it.

```
hd.py             the loop: next(change), facts, records, the pass; commands below
hd.yaml           repos, paths, the agent count, the context limit, the fork's permanent pins
hook.py           SubagentStart/Stop: run start and end, then the pass started without waiting;
                  PreToolUse: a subagent may not `hd approve`; PostToolUse: hand off at the context limit
tools/track.sh    the harness track's script; tools/track.md its rules and seed rows. Each product repo holds its own
                  track the same way (the fork's on branch local/harness): build | up | down | gate | ship | measure | log
                  <slug> [T], blocking on facts; its judgment skills under its .claude/skills/
hd-public         the one program run as user `hd` with the full token (sudoers-limited): upstream acts and releases
.claude/agents/   dev.md, qa.md, orchestrator.md (cross-track planning and monitoring); .claude/skills/head/  main's loop
mcp/              osrs-mcp (cache, wiki, gamevals); the devtools front (desktop, mobile)
harness/          goals/, changes/ (definitions, committed); state/, evidence/ at the root, git-ignored
tests/test_hd.py  one class per requirement, over fakes of git, gh, docker and the process table
```

| Command | Who | Does |
|---|---|---|
| `hd` | main | prints spawns (`Agent(<role>, "Read and follow state/briefs/<run>.md")`), cards, questions, runs, goals, change facts (R7) |
| `hd approve <slug> <head>`, `hd answer <slug> <text>` | main, after the user's word in chat | approval bound to head and the PR body digest; an answer appends a contract row |
| `hd new <slug> ...` | a planning run, the user | writes a definition |
| `hd show <slug>` | agents | the definition, contract, every verdict, gate and build result, the hand-off file |
| `hd handover <slug>` | dev | reads the pushed dev ref (no sha typed), runs every `check:` row of the contract (a `tools/` script, a unittest run or `true`; anything else runs as `false`), refuses on any failure, a conflict or an empty evidence dir, records {head, T} |
| `hd verdict <slug> <head> <rows.json>` | qa | every row pass or fail, appended; refused if a row is missing |
| `hd tree <slug> <commit>` | a track script | the T commit and tree of a working-copy snapshot, so a dev builds T |
| `hd rows <slug> <T commit> <build copy>` | a track script's gate | every `check:` and `gate:` row at the track root with `BUILD` set; exit 1 names the failures |
| `hd ask <slug> <text>` | agents | refused while a question is open on the change |
| `hd tick` | the timer, the hook | one pass |

## Data

```
harness/goals/<slug>.md        slug, track, target; measured by the track's `tools/track.sh measure`
harness/changes/<slug>.md      slug, track, kind (change|release|local), priority, deps, goal, pr, finding, network, version; body
evidence/<slug>/contract.md    rules: {AGENTS.md: <blob>, CONTRIBUTING.md: <blob>}; rows `- id | text | check: <cmd> | judge`
evidence/<slug>/               accuracy.md, pr-title.txt, pr-body.md, pr-comment.md, in-game evidence, handoff.md
state/<slug>/handover.json     {head, T}                       state/<slug>/gate.json      {T, ok, detail}
state/<slug>/verdicts.jsonl    {head, contract, rows{id: pass | fail: note}, rules{file: blob}, run}   appended
state/<slug>/approval.json     {head, body}                    state/<slug>/ask.json       {text}
state/<goal>/measure.json      {tree, value, report}           state/live/tree.json        {tree, commit, heads, names}
state/runs/<name>.json         {role, change, step, input, brief, console_pid, console_start, events_at, agent_id, transcript, started, ended, record, last, usage, handoff_told}; runs/by-agent/<id> → name
state/briefs/<run>.md          the prompt; state/events.jsonl  one line per state change (rotated at 20 MB); state/wake  its size
state/<slug>/proc-<script>.json {pid, start, attempts}; repair-<name>.json {attempts}: a script or repair in flight
fork local/merge/<a>-<b>       a recorded resolution of heads a and b, used by T_int while both are current
```
T = `git merge-tree --write-tree` of the base, the dependencies' heads and the head, made a commit with `commit-tree`
so a copy can check it out; the integration tree T_int is the same over every gated open server head plus the
permanent pins. Builds are artefacts named by T: a server image `or:<T>` (jar and game cache), a client APK
`evidence/<slug>/<T>.apk` with its repack log, a harness test run. The game cache is keyed by the hash of its inputs
(OpenRS2 cache id, pack configs, gamevals) in a named docker volume. The build copy is `<repo>/.worktrees/<slug>-build`, the
dev's clone `<repo>/.worktrees/<slug>`, worktrees of the product repo; containers, volumes and client windows carry the slug or the run name.

## The loop

```
next(change):
  deps live?                        no → wait on them
  contract.md?                      no → qa run (server) | derived from the definition and seed rows (client, harness)
  handover at the dev ref's tip?    no → dev run (a hand-off file lists its successor; FAIL findings and gate details in the brief)
  T                                 conflict → dev
  build(T)                          not built → tools/track.sh build; failed → dev
  gate(T)                           not run → tools/track.sh gate (script rows, fork CI on gate/<slug> at T, probe, tests); failed → dev
  verdict(head, contract)           none → qa run; FAIL with a code row → dev; text-only rows: qa fixes the text, re-marks
  server: live.json ⊇ head?         no → ship test server (T_int built once, deployed); a pin conflict → the younger change's dev:
                                    against a change, resolve in its own branch; against a permanent pin or a union, push local/merge/<a>-<b>
  public (upstream, release)?       approval at head? no → card
  ship                              upstream: push, PR, CI green, comment naming head, ready, review requested; release: gh release; else merge and push
  wait                              upstream merged; a maintainer finding files a new change on the pr with deps [this], contract inherited plus the finding
  done
```
A contract's rule rows carry the upstream rule files' blob shas; when a sha moves, only those rows are re-judged. A reviewer is listed only where the contract has `judge:` rows (client changes have none; releases do). A
hand-over at the same head after a verdict re-marks only the failed rows. A goal's `measure` is a step of the goal:
unmet when its target's tree (client: master and the live T_int) is not the tree of `measure.json`; below target,
the orchestrator files changes.

**The pass** (`hd tick`, a systemd user timer and after every run end): fetch each remote once; for every change
compute `next`; start the script step of each change whose process is not alive (pid with start time), one ship at a
time; write an event only when `next` differs from the last event; end the runs whose console is gone and remove what
they own; repair what is observed broken, once. **Main** (skill `head`) is the chat head: a watch on `state/wake` wakes it; it runs `hd`, spawns each listed run by
path, shows each card, records the user's word, dispatches the user's other messages to the run or the orchestrator
they concern, re-arms the watch (an expiry is a wake too) and returns to the user. **The orchestrator** is a run
listed when the facts call for it (an alert, a goal below target with nothing open, fifty events since its last run):
it files the changes that close a goal's gap with dependencies across tracks, and turns an issue it observes in
operation (a run ended without its record twice, a harness-made gate failure, a needless question) into a harness
change that a harness dev run remediates. It writes no product code.
**Runs**: the brief holds the definition, contract, prior verdicts and hand-off; the role file holds the nevers; the
track file holds the rules. A dev run commits in its clone, builds with `tools/track.sh build <slug>` (the working
copy snapshotted to an anonymous commit, T computed, the build copy checked out at T, built incrementally), brings
the result up with `up <slug> [N]` (server from `or:<T>` on the change's ports, accounts seeded, N clients started and
logged in by widget actions, blocks until every devtools endpoint answers), and hands over. The hook tells a run past
the context limit to write `handoff.md` and hand back; the successor is listed with it.

**Authority**: main, the pass and every agent run as the user with a fine-grained token limited to AlexPerrin/*, so
no command of theirs can act on OpenRune or publish. The ship step of a public act runs `sudo -u hd hd-public <slug>
<head>`, the one program sudoers allows, which holds the full token and acts only when `approval.json` names that
head. The one hook rule: `hd approve` is denied inside a subagent.

| | Client | Server | Harness |
|---|---|---|---|
| Base, head | `origin/main`, `origin/client/<slug>` | upstream `main`, fork `dev/<slug>` | `main`, `harness/<slug>` |
| build(T) | host build, ninja, repack with `OPENRUNE=1 LOCAL_AUTH=1`; APK and log | Gradle in container `build-<slug>`, cache by inputs; image `or:<T>` | the test suite at T |
| gate(T) | repack log lines (checked again at install), probe report at T, network QA when `network`; `log` reads logcat by pattern since a marker | script rows (gameval ids unique across T_int, dupe tests per item-moving module, evidence files, trailers), fork CI on `gate/<slug>` | tests; `hd tick --dry-run` plans no upstream action main's pass does not |
| judge | release only | every contract row | none |
| ship | merge `master`, push; release after the yes | test server: deploy `or:<T_int>`; upstream after the yes | merge `main`, push |

```mermaid
sequenceDiagram
  participant M as Main
  participant D as dev
  participant S as tools/track.sh
  participant P as Pass
  participant Q as qa
  participant U as User
  P->>P: contract exists, no hand-over: brief written, event
  M->>D: Agent(dev, "Read and follow state/briefs/<run>.md")
  D->>S: build <slug>: T, image or:<T>
  D->>S: up <slug> 2: server, two logged-in clients
  D->>P: hd handover <slug> (script rows pass, {head, T})
  P->>S: gate <slug> <T>: rows, fork CI
  P->>S: ship test server: or:<T_int>
  M->>Q: Agent(qa, brief)
  Q->>P: hd verdict: every row
  P->>U: card (head, rows, texts)
  U->>M: yes
  M->>P: hd approve <slug> <head>
  P->>P: ship upstream: push, PR, CI, comment, ready
```

## Run and test

```
~/.config/systemd/user/hd-tick.service   [Service] Type=oneshot  ExecStart=/usr/bin/python3 %h/osrs-harness/hd.py tick
~/.config/systemd/user/hd-tick.timer     [Timer] OnBootSec=1min  OnUnitActiveSec=1min   [Install] WantedBy=timers.target
loginctl enable-linger alex && systemctl --user enable --now hd-tick.timer
/etc/sudoers.d/hd-public                 alex ALL=(hd) NOPASSWD: /home/alex/osrs-harness/hd-public   (user hd holds the full token)
python3 hd.py                            # a pass, then the view
python3 hd.py tick --dry-run             # the view, nothing started or recorded
python3 -m unittest discover -s tests    # one class per requirement over fakes; Tools runs the harness track script for real
fork .worktrees/harness: python3 -m unittest tools/server/test_tools.py   client .worktrees/harness-v8: python3 -m unittest tools/test_track.py
```

| Requirement | Mechanism |
|---|---|
| R1 Goals | the goal's `measure` step keyed by the target's tree; the live tree unblocks client deps; the orchestrator plans |
| R2 Flow | `nxt`, the pass, the briefs, the hook's bind and end, the wake file |
| R3 Contract | contract.md, `hd handover` and `hd verdict` refusals, records bound to T or head and contract, rule-row shas |
| R4 Authority | the two credentials, `hd-public` under sudoers, the one hook rule, ship after approval at head |
| R5 Recovery | the timer, rerunnable steps, pids with start times, repairs on observed effect, one ask per change |
| R6 Economy | artefacts keyed by T, verdicts keyed by head and contract, the agent count, events on edges, the hook's context limit, the track scripts |
| R7 Visibility | `hd` prints facts; `hd show` |
| R8 Trees | merge-tree, `local/merge/*` refs, the build copy, cache by input hash, names by slug or run |
