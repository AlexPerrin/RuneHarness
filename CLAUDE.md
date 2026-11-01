# osrs-harness

The harness that moves changes to their live targets for two products: the client (AlexPerrin/osrs-plugins-reverse:
RuneLite plugins in the official OSRS Android app, APK releases) and the test server (the OpenRune fork
AlexPerrin/OpenRune-Server and its Central AlexPerrin/OpenRune-Central-Server, contributed upstream to
OpenRune/OpenRune-Server and OpenRune/OpenRune-Central-Server). It is neither product's code.

**New session: read docs/PROBLEM.md (first principles), docs/PRD.md (R1–R8), docs/ARCHITECTURE.md (how it is built),
docs/HANDOFF.md (current state) and docs/ISSUES.md (the open ledger).** Every session and agent runs from this repo.

```
hd.py          the loop: next(change), the pass, the public act, the commands (hd | new | show | handover | rows | verdict | ask | answer | stop | close | approve | ship | tree | tick)
hook.py        SubagentStart/Stop, PreToolUse (one rule), PostToolUse (the context limit)
hd.yaml        the repos, the agent count, the context limit, the permanent pins
mcp/           osrs-mcp (cache, wiki, gamevals) and the devtools front for mobile and desktop
tools/         the harness track's script and rules; each product repo has its own tools/track.sh and tools/track.md
.claude/       agents/ orchestrator (the driver session and the user's chat), dev, qa, planner, reader (a run's read-only lookup); product repos hold the judgment skills
harness/       goals/ and changes/ (committed definitions); state/ and evidence/ at the root are git-ignored
docs/          PROBLEM.md, PRD.md, ARCHITECTURE.md, ACCEPTANCE.json, HANDOFF.md, ISSUES.md
tests/         python3 -m unittest discover -s tests   (one class per requirement)
```

Runs are spawned by the orchestrator session only (`claude --agent orchestrator`), each by the path of its brief (a run may spawn its own `reader`);
the user chats with it directly. A write to OpenRune and a client release is shown as a card in the orchestrator's console
(its head, acts and exact texts) and carried by `hd ship` only after the user's yes: their own
`! python3 ~/osrs-harness/hd.py approve <slug> <head>` in the orchestrator's window.

## Iteration protocol
docs/PROBLEM.md, docs/PRD.md and docs/ARCHITECTURE.md are the only source of truth. Every iteration reads them first,
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
- **Builds** go through the track scripts (`<repo>/tools/track.sh build <slug>`), never by hand in a clone.
- **Denied actions**: don't work around them; report them in the hand-back.
