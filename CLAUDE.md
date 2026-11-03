# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server, its Central AlexPerrin/OpenRune-Central-Server and its cache library
AlexPerrin/OpenRune-FileStore, contributed upstream to OpenRune/OpenRune-Server, OpenRune/OpenRune-Central-Server and
OpenRune/OpenRune-FileStore). It is neither product's code.

**New session: read docs/V9-PROPOSAL.md (the v9 design: PROBLEM, PRD, ARCHITECTURE with schema, state machine and
module skeletons), then docs/V9-BRIEF.md (what v8 did, measured). v8 as built, its docs and its 421 change definitions
are on branch `v8` (merged into `main`), context only.** Every session and agent runs from this repo.

```
harness/hd.py  the commands (thin): hd | tick | new | fold | show | row | handover | verdict | ask | answer | triage | hold | approve | close | ship | artefact | step | fault | dismiss | stop | scope | regate | kpi | commit | restart
harness/store.py the ledger: SQLite schema, migrations, the Ledger read view; the only module that opens state/hd.db
harness/observe.py world → ledger: fetch, refs, landed, GitHub (ETag), procs, docker, alerts
harness/decide.py ledger → Step: next(change) over the ordered guards, plan() for the pass; pure, no subprocess
harness/act.py Step → world: trees, keys, scripts in systemd scopes, integration merges, briefs, the wake
harness/carry.py the card (recorded acts and texts) and the carry (logged steps, resume)
harness/kpi.py hd kpi: one query per harness metric
harness/hook.py SubagentStart/Stop, PreToolUse (approve/close denied, the scope line), PostToolUse (the context limit)
hd.yaml        the repos, the agent count, the context limit, the held band, the pins
mcp/           osrs-mcp (cache, wiki, gamevals) and the devtools front for mobile and desktop
tracks/        one directory per repo: track.sh (build | up | down | gate | ship | measure | log | test | recipe), track.md (rules, seed rows), scripts; the product repos hold product code only
.claude/       agents/ orchestrator (the driver session and the user's chat), dev, qa, reader (a run's read-only lookup); skills/ the judgment skills of every track
harness/       goals/ and changes/ (committed definitions; the open v8 changes are copied in at the cutover) beside the modules above; state/ and evidence/ at the root are git-ignored
docs/          V9-PROPOSAL.md (the design), V9-BRIEF.md (v8 measured); PROBLEM.md, PRD.md and ARCHITECTURE.md are rewritten from the proposal as the build lands
tests/         python3 -m unittest discover -s tests   (decide over recorded ledger snapshots; store, observe, carry, hook small)
```

Runs are spawned by the orchestrator session only (`harness/orchestrator.sh`, which runs `claude --agent orchestrator`), each by the path of its brief (a run may spawn its own `reader`);
the user chats with it directly. A write to OpenRune and a client release is shown as a card in the orchestrator's console
(its head, acts and exact texts) and carried by `hd ship` only after the user's yes: their own
`! python3 ~/osrs-harness/harness/hd.py approve <slug> <head>` in the orchestrator's window.

## Iteration protocol
docs/V9-PROPOSAL.md is the source of truth until docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md are rewritten from it; then they are. Every iteration reads them first,
reduces the work surface (fewer concepts, steps, special cases, files, knobs), and updates them last, each fact in the
one document that owns it. PROBLEM and PRD state the workflow in its simplest terms (agents build a complete PR → the user reviews it as text in the console and says yes → it is carried upstream → maintainer feedback becomes changes on that PR), so ARCHITECTURE can change
without brittleness: every fix finds its root cause against that workflow and fixes it there, rewriting the mechanism
when the cause is in its design; a limit found is a bug of the change on its mechanism, never passed on. Code, tests, config keys and docs traceable to no requirement are removed.

## Rules
- The user's OK only for OpenRune upstream actions and client releases.
- Commits pathspec-only, authored as Alex Perrin <44126061+AlexPerrin@users.noreply.github.com>, ending with the
  Claude co-author line only (no Claude-Session line).
- Harness changes are changes of the harness track (a dev run in a worktree, a test per requirement touched) or this
  session's own commits.
- Decide on observable facts, never on time estimates; one simple mechanism over stacked rules.
- Docs state current truth only: no revision justification, history or dated rationale. A quick fix lands at once and
  is not logged; a root cause or a rewrite too large for the run goes to docs/ISSUES.md alone (short, newest first),
  cleared at each hand-off. Docs live in docs/; CLAUDE.md and README.md are the only root docs.
- The orchestrator never enters a worktree (EnterWorktree).
- Times for the user are US Eastern.
- Hooks live in the committed `.claude/settings.json`, never the personal `settings.local.json`.

## Shared rules (every role, both products)
- **Evidence** goes in `evidence/<slug>/` of this repo, never a session scratchpad.
- **Testing tools over screenshots**: mobile, desktop and server state is read through the MCP data tools
  (`osrs-devtools-mobile`, `osrs-devtools-desktop`, `osrs-mcp`) and the track scripts' `log`; a screenshot only when
  no data tool answers, or as evidence of how something is drawn.
- **Accuracy**: server behaviour must match the official server; a divergence is fixed, never recorded.
- **Privacy**: no mobile or desktop ever contacts Jagex or RuneScape servers. Every APK goes through the telemetry patch with
  `OPENRUNE=1 LOCAL_AUTH=1`; the client track's build refuses to keep any other. Never put the user's email or
  personal identifiers in HTTP requests.
- **The user's own RuneLite** (C:\Users\Alex\.runelite) is never read or modified.
- **Tester account**: never ::empty it, keep its GE offer (lobster), drop only items you spawned.
- **Processes**: only stop processes you started; the track script's `down` stops yours.
- **Builds** go through the track scripts (`tracks/<repo>/track.sh build <slug>`), never by hand in a clone.
- **Denied actions**: don't work around them; report them in the hand-back.
