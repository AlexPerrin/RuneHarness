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
| `harness/store.py` | real: the full schema as migration 1, `connect()`, `migrate()`, the `Ledger` read view; `tests/test_store.py` passes |
| `harness/decide.py` | the `Change`, `Step`, `Action`, `Cfg` dataclasses, `next()` over `GUARDS`; every guard, `priority()` and `plan()` are documented stubs |
| `harness/observe.py`, `act.py`, `publish.py`, `kpi.py` | signatures and docstrings only |
| `harness/hd.py` | the argparse command table; every command raises |
| `harness/hook.py` | the four handlers as stubs; `main()` answers `{}` on an unwritten handler, so a session in this checkout works |
| `harness/orchestrator.sh` | the five-line supervisor, final |
| `.claude/agents/` | orchestrator.md final; dev.md, qa.md, reader.md short and usable, to be finished with the brief format |
| `tracks/harness/` | `track.sh` answers only `recipe`; `track.md` has the two seed criteria |
| `tracks/client`, `tracks/fork`, `tracks/central`, `tracks/filestore`, `tracks/devtools`, `.claude/skills/` | **empty**: copy from the tools branches (below) |
| `harness/goals/` | client-api.md, server-content.md (its body still describes the old PASSES mechanism), server-content.json |
| `harness/changes/` | empty until the cutover |
| `hd.yaml` | repos, `builds`, `agents`, `context_limit`, `hold`, the 45 `pins` |
| `tests/mermaid_parse.mjs` | checks every mermaid block of a markdown file; setup in its header |

## Build order (docs/V9-PROPOSAL.md §3; each phase ends on an observed fact)

**Phase 1, the loop on the harness track.** The proof: v9 ships a harness change to itself through its own loop.
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

**Phase 2, the server track** (criteria → dev → build → gate → judge → staging → card → approve → publish →
finding). Copy `tools/` of `~/src/OpenRune-Server/.worktrees/harness` into `tracks/fork/` and its `.claude/skills/`
into `.claude/skills/`; add `recipe`, replace `hd rows`/`hd artefact`/`up.json` writes with `hd job`, `hd step` and
the `stack` table; create `staging` on the fork from upstream `main` plus the pins. `publish.py` and the
`finding`/`triage` path. Proof: a P2 change to a ready PR after the user's yes, a maintainer finding answered through
the criterion path, and a publish killed after its push step resuming with the approved texts.

**Phase 3, the client track**: copy `~/osrs-plugins-reverse/.worktrees/harness-v8/tools/` into `tracks/client/`
and its skills; the mobile bridge stays in the client repo. Proof: one client change live on `main`.

**Phase 4, alerts and KPIs**: `kpi.py` queries; the alert kinds; a goal gap listing a plan-mode dev run.

Central, FileStore and Developer-Tools tracks (ARCHITECTURE §11) follow the fork's shape once the fork works.

## Rules that bind you

- CLAUDE.md "Rules" and "Shared rules" apply unchanged. Two public acts need the user; you never do either.
- Never touch the live checkout, its timer, its orchestrator, its `state/`. Read them.
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

## Known gaps

- `tracks/*` and `.claude/skills/` are declared in ARCHITECTURE and CLAUDE.md but empty on this branch.
- `harness/goals/server-content.md` describes the old measurement; rewrite its body when the ledger query exists.
- The `devtools` repo (OpenRune-Developer-Tools) is in ARCHITECTURE §11 but not yet in `hd.yaml`; the fork of it does
  not exist yet.
- Nothing in v9 has run against the real repos. Every number in the KPI table is a target, not a measurement.
