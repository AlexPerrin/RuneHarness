# HANDOFF

The brief for a fresh console session. Read CLAUDE.md, docs/PROBLEM.md, docs/PRD.md, docs/ARCHITECTURE.md, then
docs/ISSUES.md, the open ledger for v8. Live state is what `hd` prints; none of it is kept here.

## Start prompt
Start the session in ~/osrs-harness on branch `main`. Read CLAUDE.md and docs/HANDOFF.md, then the memory files named
under Standing rules. Run `python3 hd.py` and follow skill `drive`: spawn each listed run with the Agent tool, the
brief file's text as the prompt and the role as the agent type; show cards and questions; record the user's yes with
`hd approve` and answers with `hd answer`. Nothing is pushed upstream or released without the user's yes in chat.
A quick fix lands at once; a root cause or a rewrite too large for the run is one entry in docs/ISSUES.md for v8.

## What is live
v7 ran 2026-10-25 → 2026-10-31; v8 is next (read docs/V8-BRIEF.md first). The pass runs from the systemd user timer
`hd-tick.timer` and is **paused** (`harness/state/paused`): remove the file to resume. The dashboard is
http://localhost:7790 (unit `hd-dashboard.service`). The devtools MCP servers are `osrs-devtools-mobile` and
`osrs-devtools-desktop`, both through `mcp/devtools_bridge.py` (they connect with no client running).

State at the pause (2026-10-31, US Eastern evening); `hd` is the live truth:
- **goblin-diplomacy-review-367-fftgsrq** (#367): head 77ac377e4 FAIL, 2 findings (pr-comment.md describes intermediate
  commits; `ARMOURS` should read cache category 528). Queued, not spawned: dev run -24. Also fails the new dupe check
  (GoblinDiplomacy.kt moves items without a dupe test).
- **hunter-feat-pr**: head b3209ffc9 FAIL, 5 findings plus sourcing; scope answer B (Misc items and goat luring). Fails
  the dupe check (26 files). Queued for the next dev run.
- **server-friends-chat-clan-channels**: head b8bdf662e handed over, awaits gate and review; integrator run -12 queued
  for a train failure, not spawned.
- **server-clan-channels** (clans core, settings folded in): 5e6344c7b handed over, awaits gate. Depends on friends
  chat; `MessagePublicHandler.kt` conflicts with it textually, so the train needs that resolution recorded.
  server-clan-guest → server-clan-broadcasts and server-clan-hall (P3) follow it, not started.
- **server-sidecar-jav-config-local-auth** (P0, privacy): filed; the sidecar's jav_config names Jagex hosts. Not started.
- #354, #355, #367 (the original) are merged. Live test server: integration f331350.
- Agent retros (QA and dev friction) are `evidence/<slug>/retro-<run>.md`; their themes are in docs/V8-BRIEF.md §4.

## Open decisions for the user
- Eleven `fin/*` fork branches hold finished, test-server-live work never contributed (diaries, doric, fairy-rings,
  farming, grand-exchange, jewellery, op-overrides, plank-sack, quest-test-fixture, rune-pouch, vampyre-slayer): the
  source of the rebuilt backlog, one change per feature, after the open PRs settle.
- `harness/state.v6/` (the v6 records) is kept until a server change completed a full v7 pass; then delete it.

## Standing rules
The user's rules are the memory files in `/home/alex/.claude/projects/-home-alex-osrs-harness/memory/` (index
`MEMORY.md`); read the ones named:
- Docs and process: `feedback_three_source_docs.md`, `feedback_docs_roles.md`, `feedback_harness_self_contained.md`,
  `feedback_redesign_over_patch.md`, `feedback_no_quick_fixes.md`, `feedback_atomic_not_timed.md`,
  `feedback_targeted_tests.md`, `feedback_no_source_of_truth_in_rewrite.md`.
- Upstream: `feedback_approvals_in_chat.md`, `feedback_gate_before_upstream.md`, `feedback_ready_procedure.md`,
  `feedback_ready_means_mergeable.md`, `feedback_upstream_pr_no_deferral.md`, `feedback_settle_existing_prs_first.md`,
  `feedback_upstream_rules_revisable.md`, `feedback_fewer_tests_upstream.md`, `feedback_pr_body_checkboxes.md`,
  `project_pr_contribution_model.md`, `project_fork_staging.md`.
- Layout and clients: `project_repo_isolation_layout.md`, `project_no_device_locking.md`.
- Client releases: `project_client_versioning.md`, `project_single_apk.md`.
- v7: `project_v7_agents_via_agent_tool.md`, `project_v7_cutover.md`.

## Gotchas
- Hooks are read at session start: after a change to `.claude/settings.json`, restart the console (the SubagentStart
  hook was removed on 2026-10-25; a console started before that still runs it, harmlessly). The hook program itself
  (`hooks/hook.py`) is read on every event, so its edits apply at once.
- A run ends when its agent calls SubagentHandback; a stop without one is a pause (background build). An agent that
  dies without a hand-back stays `running` in the list: end it by deleting `harness/state/runs/<name>.json`.
- The auto-mode classifier denies the console `kill` and deleting pushes even where the guard allows them; the user
  runs those with the `!` prefix.
- `systemctl --user` needs `XDG_RUNTIME_DIR=/run/user/1000` in a non-login shell (WSL); linger is enabled.
- Upstream merges often: every merge voids every gate (bound to base), so all open changes re-gate on fresh scratch
  merges; the fork CI load is one run per open change per upstream merge.
- WSL to Windows interop (adb.exe, desktop bridge) times out intermittently: retry. The devtools MCP servers often do
  not connect; `tools/devtools_mcp.py --call` and the desktop bridge script work.
- `qa.sh` dev lane: spotless cannot run in a git worktree inside the container (no `.git` dir visible), so a merged
  tree for the dev lane is a shared clone (`agents/<name>/or-run`); a clone dir recreated under a warm `qa-dev-<owner>`
  container leaves a stale mount ("outside of container mount namespace"): remove that container first.
- The guard denies the console `bash -n train/train.sh` too (the train scripts are the pass's): check shell syntax by
  reading, or in a test.
