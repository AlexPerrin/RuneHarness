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

## Where the loop stands (hand-off of 2026-11-03 12:30Z)

Every mechanism of ARCHITECTURE is built, unit-tested (`tests/`, 57 tests; the track suites `tracks/fork/server/test_tools.py`
102 and `tracks/client/test_track.py` 29) and documented. The loop runs live from this worktree: `harness/orchestrator.sh`
in the user's terminal (the orchestrator on Sonnet 5.5, autonomous: spawn, TaskStop, restart; dev and qa on Opus 5.5;
`agents: 5`), `hd-loop.timer`, `state/hd.db` (migration 5). The user chats with this engineer session (one-off, for the v9
build); the design's user console is the driver (`.claude/agents/driver.md`, manual: shows, records the user's words,
one-off changes on their word). Proven live:

- harness track: fourteen changes shipped by fast-forward (dev runs, gate: tests, replay over the live definitions, both
  track suites; ship under `state/ship.lock`, shared with `hd commit`); alerts filed and dismissed; T5 six times; `hd close`
  ending a run's agent; an agent interrupted in its console ended by the pass from its transcript, its successor listed.
- fork track: `server-training-bow` (OpenRune #444) the whole way to PR OpenRune/OpenRune-Server#450 (criteria, dev, build,
  gate with fork CI, FAIL then PASS verdict, the first `staging` from upstream main + the 11 pins, card, approval, publish:
  push, draft PR, CI, one comment, ready). The staging deploy builds the image and refuses without `state/live/key`
  (the cutover's first deploy; its `attempts` alert dismissed).
- central track: `central-rights-test-mod` (fork-only: upstream main's RightsTest does not compile; upstream PR #5
  carries the same fix) built, gated and judged PASS: the first central-track change. `central-token-login-op` (the token
  LOGIN op, 0485930 from v8) is in its dev/build.
- lab track (`tracks/lab`, repo AlexPerrin/pr-lab, its own upstream): two changes went criteria → dev → gate → card in
  two minutes; cards 2 (`lab-ci-red`: CI red → dev → second card) and 3 (`lab-hello`: happy path, then the user merges
  and the loop must see it land) wait for the user. Kill a publish after its push for A2's resume proof.
- client track: the measure falls back to a RuneLite desktop; the probe's `Client.stopNow()` ends the client, so the
  measure's wait ends when the client is gone (fac3b3e); `client-probe-no-stop` (dd3d04d, verified on the desktop) waits
  on the Android chain below before its mobile criteria.
- goals: `server-content` 0% on staging; its plan run filed 17 F2P quest changes, held at P4 (the user: content for its
  own sake is the stretch goal); Cook's Assistant closed (upstream #445). `client-api` unmeasured until the probe fix ships.

The Android chain (P1, the user's first priority): `client-probe-no-stop` ← `server-android-token-login` (453a45e in
its gate; the official app's token is refused by the live verifier, cause uncaptured) ← `central-token-login-op`
(Central maps a verified token to its account; dev run 64) ← `central-rights-test-mod` (done). `h-desktop-login-error-dialog`
(P1): after a refused token the desktop sits on the login error dialog; the judge of the token change needs it.

Of the 29 requirements, 27 have every proof observed; pending: A2's killed publish resuming (test it on a lab card),
A3 a maintainer finding answered (needs a login that is not AlexPerrin, or #450's first comment).

## Next, toward the goal (a harness tested end to end; the PRD validated)

1. **Lab cards 2 and 3**: approve, kill one publish after its push, merge lab-hello's PR on GitHub; the loop must record
   `ci-failed` → dev → second card, the resume, and the merge landing the change. Replace the `pending:` in ACCEPTANCE.
2. **Android**: the chain above; the fix reaches the mobile only through a live deploy (every APK carries the live
   modulus), so the cutover is on its path. Then `client-probe-no-stop` ships, the measure lands a value, the plan run
   files client changes.
3. **A3**: a maintainer comment on #450 → triage → criterion → dev → one comment.
4. **State lifetime** (a `clean` verb per track when a change is done or closed), the `kpi` alert, the regression reprint,
   the as-is submission for a quest found 1:1: after the goal.
5. **Cutover** (below), the user's decision; the open v8 changes carry over as changes.

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
  `tests/mermaid_parse.mjs`. Commit with `hd commit <paths> -m "<message>"`: it holds `state/ship.lock`, so a ship's
  candidate is never computed on a tip your commit then moves (a bare `git push` raced three ships).

## Only the user decides

- The default decisions in docs/V9-PROPOSAL.md §5, in particular: scripts and skills in this repo (11), tree-only
  keys with `hd regate` (1), the real `staging` branch (3), no monitor and no planner (5), the shared GitHub token (9).
- The cutover: which open v8 definitions carry over (`git ls-tree v8 harness/changes`, 47 of 421 closed; most
  harness ones are obsolete), stopping the v8 timer and orchestrator, merging `v9` into `main`, running `hd submit`
  once per carried change with an existing dev tip, and the first re-judge of each open server change.
- The Central upstream hold, the P3 band hold (`hold: P2` in hd.yaml), and every card.

## Since the last state (2026-11-07 01:45Z)

`h-retention` shipped (PRD H7): owner rows, release in the pass, a disk level. One Gradle home per build slot, not one
shared volume. The pre-existing worktrees were adopted once; the rest of the host's artifacts carry owners from their next
build. `C:\\osrs-test` was deleted by the hand disk cleanup and is rebuilt by `tracks/fork/server/desktop_template.sh`; a
fresh template's first desktop downloads RuneLite and has no profile, which no run has exercised yet. A run ends with its
orchestrator session (a usage limit ended one and left four runs live for three days). Pending the user: Hunter's question
4, the triage of 15 maintainer comments on #354 and #367.

## The cutover (started 2026-11-03 15:00Z on the user's word)

Done: v8's `hd-tick.timer` disabled (its orchestrator was already gone); ten v8 changes carried as v9 definitions and
submitted at their v8 heads (server-token-auth, cannon #354, hunter #408, goblin #367, server-cache-clientscript-name-hash;
fork-only world-entities, npc-examine-without-overlay, levelup-guide-messages; friends-chat and clan-channels under the
social hold); the three PR branches left the pins; v8's quest heads noted on the P4 quest changes. Their criteria runs and
re-judges proceed through the loop.

Left, in order:
1. **The live key, once server-token-auth is on staging.** Copy `~/osrs-harness/state/live/` (`key/`, `tree.json`) into
   this checkout's `state/live/`. Not before: staging without the token verifier would drop token login (desktop
   `up token`, Android) from the live server. The next pass then deploys staging, which marks its changes `live`;
   `client-probe-no-stop` and the Android check on live follow.
2. **The runtime move, at the user's desk** (it restarts the orchestrator in their pane): stop `harness/orchestrator.sh`
   (the session's `/exit`) and `hd-loop.timer`; `sqlite3 .backup` this `state/hd.db` into `~/osrs-harness/state/hd.db`;
   `git -C ~/osrs-harness merge v9` (main has one commit v9 lacks, cbe98a9, the merge of PR #2 from v8, with no file change against v9's base: a plain merge), hd.yaml `harness.base: refs/heads/main`, commit,
   push; copy `state/<slug>/`, `state/briefs/`, `state/live/` across; start `harness/orchestrator.sh` from
   `~/osrs-harness`; then `git worktree remove` this worktree.

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
