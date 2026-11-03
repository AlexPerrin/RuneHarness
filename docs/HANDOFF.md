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
| `harness/decide.py` | real: every guard; one deploy per staging tree in `plan()` |
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
| `harness/goals/` | client-api.md, server-content.md, server-content.json |
| `harness/changes/` | empty until the cutover |
| `hd.yaml` | repos, `builds`, `agents`, `context_limit`, `hold`, the `pins` |
| `tests/mermaid_parse.mjs` | checks every mermaid block of a markdown file; setup in its header |

## Where the loop stands (hand-off of 2026-11-03 06:00Z)

Every mechanism of ARCHITECTURE is built, unit-tested (`tests/`, 49 tests; the track suites `tracks/fork/server/test_tools.py`
102 and `tracks/client/test_track.py` 29) and documented. The loop runs live from this worktree: `harness/orchestrator.sh`
in the user's terminal (the orchestrator on Sonnet 5.5, autonomous; dev and qa on Opus 5.5; `agents: 5`), `hd-loop.timer`,
`state/hd.db` (migration 5). The user chats with the engineer session (this hand-off's role); the design's driver console
(`.claude/agents/driver.md`) is the long-term shape. Proven live so far:

- harness track: eight changes shipped by fast-forward through dev agents, gate (tests, replay over the live
  definitions, both track suites) and ship; alerts filed and dismissed; the T5 lifecycle six times (bind, drain on a
  moved definition, `hd restart`, the supervisor's next iteration); `hd close` ending a run's agent (the hook denies it
  every tool).
- fork track: `server-training-bow` (OpenRune #444) the whole way: criteria run, dev run, cached build, gate with fork
  CI, a FAIL verdict (6 criteria) → dev → PASS verdict (run 25), the first `staging` (upstream main + the 11 pins;
  two pins rebased by hand after a `pin-conflict` alert), its merge and landing, the card, the user's approval and the
  publish: push, draft PR OpenRune/OpenRune-Server#450, CI, one comment, ready (A2 live). The staging deploy builds the
  image and refuses without `state/live/key` (alert `attempts`, dismissed: the cutover's first deploy).
- client track: the client-api measure fell back to a RuneLite desktop (`h-measure-desktop`) and logged in; the API
  probe then called `Client.stopNow()`, which stops the client, so no report came. The measure's wait now ends when the
  desktop's client is gone (fac3b3e); the probe fix is the client change `client-probe-no-stop` (run 35 live).
- goals: `server-content` measured 0% on staging; its plan run filed 17 F2P quest changes at P2 (the user: test load
  for the harness, below the Android work). `client-api` has no measure yet (the probe).

In flight (`hd tick --dry-run`): `server-android-token-login` (P1, fork): the official Android app's token login is
refused by the live server's verifier while the issuer's sign-in completes and both secrets match (the token the app's
login block carries was never captured; mobile reaches only the live stack). The quests' criteria and dev runs.
`server-training-bow` waits on maintainers (#450). The 26 v7-era pins were dropped (562b5c5): what is wanted returns
as a change.

## Next, toward the goal (a harness tested end to end; the PRD validated)

1. **Android auth** (`server-android-token-login`): the fix reaches the mobile only through a live deploy, so the
   cutover (below) is part of its path. Its dev run captures what the app sends under LOCAL_AUTH and fixes the verifier
   or the issuer's response shape; the desktop token login (`track.sh up token`) must keep working.
2. **Client, to a ship.** `client-probe-no-stop` ships to the client's `main` → the measure runs on the desktop
   fallback and lands a value → below 100 lists the plan run (`goal:client-api`), which files client changes.
3. **A3 and the resume case.** A maintainer comment on #450 → triage → a criterion → a dev → one comment; a publish
   killed after its push resuming (A2's last pending). Replace each `pending:` in docs/ACCEPTANCE.json with the fact.
4. **State lifetime.** Nothing removes a done change's `state/<slug>/`, its clone and build copy under the repo's
   `.worktrees/`, or its `or:<tree>` images (v8 left 3.7 GB and 67 worktrees). The proposed rule: a change's working
   state lives while the change is open; done or closed with its stack down, the pass removes them (a `clean` verb per
   track), keeping evidence, the ledger and `state/live/`. A harness change after the goal.
5. **Cutover** (below), the user's decision; `server-token-auth` and the other open v8 changes carry over as changes
   (their heads are no longer pins).

## Rules that bind you

- CLAUDE.md "Rules" and "Shared rules" apply unchanged. Two public acts need the user; you never do either.
- Never touch the live checkout, its timer, its orchestrator, its `state/`. Read them.
- A script of the checkout the loop runs from changes only by a ship (git replaces a file by rename, so a running bash
  keeps the old one): an in-place write to a running track script moves it under bash and ends it with a syntax error.
- The orchestrator session runs this worktree's working copy: every saved edit is live at its next `hd`. Keep the tree
  importable between commits; commit small; the replay compares a candidate with its merge base, so your own commits
  do not fail others' gates.
- The shell of a session resets its cwd to `~/osrs-harness` (the live checkout) after a command that ends elsewhere:
  use absolute paths into this worktree; never write under `~/osrs-harness`.
- Claude Code snapshots hook matchers at session start: a hook change is tested by a fresh session (the orchestrator
  restarts itself on a moved definition; a hook change needs `hd restart` by hand).
- An alert is the user's to dispose of, through the driver console. In this engineering session you fix it at once as
  your own commit and `hd dismiss <id>` naming it, or file it with `hd new --from-alert <id>` on the user's word. Never
  both. The engineer role is this hand-off's only; the design has the driver and the autonomous agents.
- Commit a definition the orchestrator filed (`harness/changes/*.md`) if it did not (`hd commit`).
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
5. The first checked server head creates `staging` from upstream main plus the pins; a pin that no longer merges
   is alert `pin-conflict` naming it: rebase that pin branch on the fork and the next pass creates staging whole.
6. The deploy of staging replaces the live test server (`osrs-openrune`) with staging's image, keyed on the live
   pair; the first deploy is the moment the test server moves from v8's integration tree to staging.

## Known gaps

- `tracks/central` and `tracks/filestore` are built from their repos (in-process Central; FileStore's modules named as
  their artefacts) but have not run against a real change; `tracks/devtools` waits for the fork of
  OpenRune-Developer-Tools, which does not exist yet.
- The `kpi` alert (a metric past its target) is not computed; `hd kpi` prints the metrics.
- `tests/mermaid_parse.mjs` needs `npm i mermaid jsdom` in `~/.cache/mm` (its header); run it with
  `NODE_PATH=~/.cache/mm/node_modules`.
- The `devtools` repo (OpenRune-Developer-Tools) is in ARCHITECTURE §11 but not yet in `hd.yaml`; the fork of it does
  not exist yet.
- Only the harness track has run against its real repo. Every number in the KPI table is a target, not a measurement.
