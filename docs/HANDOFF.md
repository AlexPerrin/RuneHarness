# Hand-off to the v9 harness dev

The architect's hand-off: what exists, what to read, what to build first, and what only the user decides.

## Where things are

- **v8 is live** from `~/osrs-harness` on branch `main` (`307daa8`, "Merge v8 into main"): the `hd-tick.timer` runs
  its pass and a `claude --agent orchestrator` session drives it. Never edit, check out or run anything in that
  checkout. Its `state/` (3.7 GB: `events.jsonl`, `runs/*.json`, briefs, logs) and `evidence/` are read-only
  context and your fixture source.
- **v9 is this worktree**, `~/osrs-harness/.worktrees/v9`, branch `v9`, pushed to `origin/v9`. Work here. Commit on
  `v9` and push it as you go (pathspec commits, authored as Alex Perrin, the one co-author line).
- The product repos: `~/osrs-plugins-reverse` (client), `~/src/OpenRune-Server` (fork; `~/src/openrune-work/<slug>`
  were v8's per-change clones), `~/src/OpenRune-Central-Server`, `~/src/OpenRune-FileStore`. v8's track scripts and
  skills sit on their tools branches, checked out at `~/osrs-plugins-reverse/.worktrees/harness-v8` and
  `~/src/OpenRune-Server/.worktrees/harness`.

## Read, in this order

1. `docs/PROBLEM.md`: what a harness is for (memory, hands, gate, tempo), the workflow, the goals.
2. `docs/PRD.md`: the 29 requirements (M, H, G, A, T), each naming its mechanism.
3. `docs/ARCHITECTURE.md`: the ledger schema, the change state machine and guards, the pass, the modules, the
   commands, the roles, the alert kinds, the orchestrator's lifecycle, tracks and repos, goals.
4. `docs/V9-PROPOSAL.md`: what v8 had that v9 does not, the KPI targets, the build plan, the inheritance audit,
   the default decisions the user may still overturn.
5. `docs/V9-BRIEF.md`: v8 measured, with the file layout of its state (your fixtures) and its root causes.
6. v8 itself when you need a mechanism's detail: `git show v8:hd.py`, `v8:hook.py`, `v8:docs/ARCHITECTURE.md`.

## What exists on v9

| file | state |
|---|---|
| `harness/store.py` | real: schema (migration 1), `connect()`, `migrate()`, `event()`, `alert()`, the `Ledger` read view |
| `harness/decide.py` | real: every guard but `measure_due` and `plan_due` (phase 4, marked `shortcut:`); one deploy per staging tree in `plan()` |
| `harness/observe.py` | real: `fetch` (with trees), `landed`, `procs`, `sessions`, `alerts`, `texts`, `transport`/`gh` (ETag), `pr` (findings, merged), `checks`; `docker` raises |
| `harness/act.py` | real: `cfg()`, `changes()`, `candidate()`, `seed()`, `clone()`, `brief_text()`/`brief()`, `start()`, `wake()`, `tick()`, `tick_later()` |
| `harness/hd.py` | real: every command of ARCHITECTURE §8; `gate`, `candidate` and `stack` added for the track scripts |
| `harness/hook.py` | real: SessionStart/End, PreToolUse (deny, bind, scope line), PostToolUse (bind, context limit), SubagentStop (the record line, the one refusal) |
| `harness/kpi.py` | eight queries; the rest of the metrics follow the phase that produces their rows |
| `harness/publish.py` | real: the card (acts and texts from the observed PR and the text rows), the approval, the resumable publish; `tests/test_publish.py` over a fake transport |
| `harness/orchestrator.sh` | final: the session in a user scope, the `hd-loop` minute timer started once |
| `.claude/agents/` | orchestrator.md (relative paths), dev.md, qa.md (hd is the brief's command), reader.md |
| `tracks/harness/` | `track.sh` (recipe, test, gate, ship), `replay.sh`, `track.md`: seeds tests, replay, fork-tools, client-tools |
| `tracks/fork/`, `tracks/client/` | the tools branches' scripts adapted (no TOOLS_ROOT copies, `hd candidate`/`hd gate`/`hd job`/`hd stack`, build slots by flock, `deploy` of staging, a client `ship` that fast-forwards main); their suites pass (103 and 28 tests) |
| `.claude/skills/` | accuracy, dupes, pr-text, probe, qa-server, network-qa, qa-client, reverse, in v9 vocabulary |
| `state/hd.db` | the ledger of the three phase-1 changes (h-kpi-track by hand, h-test-warnings and h-agent-hd by dev agents): the first fixture source for `tests/fixtures/` |
| `tracks/client`, `tracks/fork`, `tracks/central`, `tracks/filestore`, `tracks/devtools`, `.claude/skills/` | **empty**: copy from the tools branches (below) |
| `harness/goals/` | client-api.md, server-content.md (its body still describes the old PASSES mechanism), server-content.json |
| `harness/changes/` | empty until the cutover |
| `hd.yaml` | repos, `builds`, `agents`, `context_limit`, `hold`, the 45 `pins` |
| `tests/mermaid_parse.mjs` | checks every mermaid block of a markdown file; setup in its header |

## Build order (docs/V9-PROPOSAL.md §3; each phase ends on an observed fact)

**Phase 1, the loop on the harness track: built.** Three harness changes shipped through the loop from this
worktree (`git log v9`: 5f05598, 7f7f7e3, 3952ed1), two of them by dev agents spawned with the printed `Agent(dev, …)`
call. Still to observe in a fresh session started by `harness/orchestrator.sh` (hooks are snapshotted at session
start, so the dev session that built this could not exercise them): the Read binding, the `hd scope` prefix on each
Bash command, SessionStart/End, drain and `hd restart`. The agents' hand-backs were bound through the record-line
path, which the same hook also serves.
1. `observe.fetch` and `landed` over the real repos; `procs`; `alerts` as SQL.
2. The guards of `decide.py`, in order, each a few lines over `Ledger`; `plan()`. Write `tests/test_decide.py`
   against a fixture ledger you build by hand first, then against a `.backup` of your own `state/hd.db` once it has
   content.
3. `act.candidate`, `key`, `start` (systemd scope, the `builds` flock semaphore), `brief`, `wake`, `tick`.
4. `hd.py`: `tick`, `new`, `show`, `submit`, `job`, `step`, `stop`, `scope`, `kpi`, `commit`, `restart`,
   `session-ended`. The view is a delta per session (`session.seen_event`).
5. `hook.py`: bind on SubagentStart, end on SubagentStop (the one-line hand-back), the two denials and the scope
   line, the context limit.
6. `tracks/harness/track.sh`: `test`, `gate` (tests + replay), `ship` (fast-forward `v9`).
7. Run `harness/orchestrator.sh` from this worktree with a fresh `state/hd.db`, file one harness change with
   `hd new`, and let the loop take it to `landed`.

**Phase 2, the server track: built, proof pending.** The scripts, skills, staging merge, deploy of staging, PR
observation, findings, triage, card, approval and publish exist and are unit-tested (the publish over a fake
transport: killed after a step, it resumes with the card's texts). Observed live so far: a fork-only probe (f-probe)
whose dev built the candidate through `tracks/fork/track.sh build`. Still to observe: the gate job (spotless, gamevals,
gate-ci on the fork), a judge run with desktops, the first staging merge (which creates `staging` from upstream main
plus the pins: a pin that no longer merges is alert `pin-conflict`), and the upstream proof (a P2 change to a ready
PR after the user's yes; a maintainer finding answered; a killed publish resuming), which needs the cutover: the
deploy script refuses without `state/live/key`, and the open PRs are v8's until then. Comment 6586756996 on PR #448
is a real triage case waiting.

**Phase 3, the client track: scripts built, proof pending.** `tracks/client/` and its skills are in; a client
build needs `state/live/key/client.key` (the live modulus), so the proof (one client change live on `main`) waits for
the cutover's copy of the live key pair.

**Phase 4, alerts and KPIs**: `kpi.py` queries; the alert kinds; a goal gap listing a plan-mode dev run.

Central, FileStore and Developer-Tools tracks (ARCHITECTURE §11) follow the fork's shape once the fork works.

## Rules that bind you

- CLAUDE.md "Rules" and "Shared rules" apply unchanged. Two public acts need the user; you never do either.
- Never touch the live checkout, its timer, its orchestrator, its `state/`. Read them.
- A script of the checkout the loop runs from changes only by a ship (git replaces a file by rename, so a running bash
  keeps the old one): an in-place write to a running track script moves it under bash and ends it with a syntax error.
- No new concept, file, knob or special case without a requirement in PRD naming it. A limit you meet in a mechanism
  is fixed in that mechanism; if the design itself is wrong, say so in the hand-back rather than patching around it.
- Docs state current truth: a mechanism you change is updated in ARCHITECTURE in the same commit; nothing about v8
  goes into PROBLEM, PRD or ARCHITECTURE (V9-PROPOSAL holds that).
- Decide on facts, never on elapsed time. A run ends only by its own hand-back, a stop, a close or its console's
  death.
- Run `python3 -m unittest discover -s tests` before every commit; check a touched doc's diagrams with
  `tests/mermaid_parse.mjs`.

## Only the user decides

- The default decisions in docs/V9-PROPOSAL.md §5, in particular: scripts and skills in this repo (11), tree-only
  keys with `hd regate` (1), the real `staging` branch (3), no monitor and no planner (5), the shared GitHub token (9).
- The cutover: which open v8 definitions carry over (`git ls-tree v8 harness/changes`, 47 of 421 closed; most
  harness ones are obsolete), stopping the v8 timer and orchestrator, merging `v9` into `main`, running `hd submit`
  once per carried change with an existing dev tip, and the first re-judge of each open server change.
- The Central upstream hold, the P3 band hold (`hold: P2` in hd.yaml), and every card.

## The cutover (the user's call; the steps once decided)

1. Stop v8: `systemctl --user disable --now hd-tick.timer` and `/exit` its orchestrator; `rm ~/.config/systemd/user/hd-tick.*`.
2. Make the live checkout v9: `git -C ~/osrs-harness merge --ff-only v9`, then in hd.yaml `harness.base: refs/heads/main`
   (commit, push) and `git worktree remove ~/osrs-harness/.worktrees/v9`. v8's `state/` stays (git-ignored); v9 writes
   `state/hd.db` beside it and reads `state/live/key` and `state/live/tree.json` as they are.
3. Definitions: for each open v8 change kept (`git ls-tree v8 harness/changes`), rewrite its front matter to v9's keys
   (`track: server` → `fork`; `pr`, `public` the PR branch; drop deps on obsolete harness changes); commit them.
4. Start `harness/orchestrator.sh` from `~/osrs-harness` (it starts `hd-loop.timer`). The first pass seeds every open
   change's criteria and lists criteria runs for the upstream ones; for a change whose dev tip already exists on the
   fork, run `hd submit <slug>` once (it records the tip and its candidate, checking nothing) before that pass, or
   right after it.
5. The first checked server head creates `staging` from upstream main plus the 45 pins; a pin that no longer merges
   is alert `pin-conflict` naming it: rebase that pin branch on the fork and the next pass creates staging whole.
6. The deploy of staging replaces the live test server (`osrs-openrune`) with staging's image, keyed on the live
   pair; the first deploy is the moment the test server moves from v8's integration tree to staging.

## Known gaps

- `tracks/central` and `tracks/filestore` are built from their repos (in-process Central; FileStore's modules named as
  their artefacts) but have not run against a real change; `tracks/devtools` waits for the fork of
  OpenRune-Developer-Tools, which does not exist yet.
- The `kpi` alert (a metric past its target) is not computed; `hd kpi` prints the metrics.
- `tracks/fork/track.sh` `up` loads the desktops' devtools jar from v8's client script (`CLIENT_TRACK` default) until
  the client track's `build live` is wired (marked `shortcut:`).
- `tests/mermaid_parse.mjs` needs `npm i mermaid jsdom` in `~/.cache/mm` (its header); run it with
  `NODE_PATH=~/.cache/mm/node_modules`.
- `harness/goals/server-content.md` describes the old measurement; rewrite its body when the ledger query exists.
- The `devtools` repo (OpenRune-Developer-Tools) is in ARCHITECTURE §11 but not yet in `hd.yaml`; the fork of it does
  not exist yet.
- Only the harness track has run against its real repo. Every number in the KPI table is a target, not a measurement.
