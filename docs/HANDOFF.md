# Hand-off to the v9 harness dev

Current state as of 2026-11-09 02:40 UTC (2026-11-08 21:40 ET). The goal: a harness implemented and tested end to end
against the workflow, with the PRD validated. Check every fact here against `hd` and the ledger before acting on it.

## Do first

1. **Unstick H8, the last `pending:` in docs/ACCEPTANCE.json (31 of 32 proved).** The chain:
   `h-ref-sign-in-no-issuer` and `h-ref-rsprox-targets` → `h-ref-embedded-central` → `h-reference-deployment`.
   Both leaves failed their gate on the replay criterion (06:09 and 06:37 UTC Nov 8: "the candidate plans differently from
   its base and evidence/<slug>/replay.md does not explain it"). `hd regate` ran on both at 17:43 UTC, yet each gate job
   row still reads failed with its 06:xx times, the gate logs (`state/<slug>/gate-<key12>.log`) were not rewritten, and
   nothing has run since: `h-reference-deployment` has waited since 17:57. Find why the regate did not take (the DELETE in
   `cmd_regate`, hd.py:590, matched the key; something put the row back or it never committed), fix it in that mechanism,
   then the leaves need a dev run to write replay.md or change the plan. `h-ref-embedded-central` passed its own gate;
   `h-ref-server-bundle` and `h-ref-pins-audit` are landed on v9. When H8 is observed, replace its `pending:`.
2. **Commit the orchestrator's definitions** it left uncommitted (`harness/changes/client-api-*.md`, `h-*.md` and the two
   modified ones in `git status`) with `hd commit`.
3. Open alert 66 (fault 284): the fork build reuses or-cache's incremental pack state across trees (`git clean -fd`
   keeps the ignored `.data/cache/incremental_server`). `h-fork-build-stale-pack-state` is filed for it.

## Where things are

- **v9 runs from this worktree**, `~/osrs-harness/.worktrees/v9`, branch `v9`, pushed to `origin/v9`: `harness/orchestrator.sh` in
  the user's terminal (peer session, dev and qa on Opus 5.5; `agents: 5`, `builds: 5`), `hd-loop.timer`, `state/hd.db`.
  Commit here and push as you go. `~/osrs-harness` (`main`) is idle v8: never write there.
- The product repos: `~/osrs-plugins-reverse` (client), `~/src/OpenRune-Server` (fork), `~/src/OpenRune-Central-Server`,
  `~/src/OpenRune-FileStore`.
- **Runs live now** (ids 304, 310–313): `h-client-build-shares-apk`, `h-mobile-loading-stall`, `client-api-login-screen-stubs`,
  `client-api-display-engine-stubs`, `h-devtools-mobile-serial`. `client-api` is measuring (e7ec3a75f909).
- `hd` with no argument runs a pass (live): read state with `sqlite3.connect('file:state/hd.db?mode=ro', uri=True)`.

## Read, in this order

`docs/PROBLEM.md`, `docs/PRD.md`, `docs/ARCHITECTURE.md`, then `docs/ACCEPTANCE.json`. `docs/V9-PROPOSAL.md` and
`docs/V9-BRIEF.md` hold the v8 context. `docs/ISSUES.md` does not exist: it is created when a root cause is too large for its run.

## The test server

Live is `04007706bd6a28377e7e338abb52660ad52962e2_c022e2f6d72a5` (deployed 19:23 UTC Nov 8 with `hunter-feat-pr`);
`state/live/tree.json` is what the running stack uses. Containers: `osrs-openrune`, `-http`, `-http-desktop`, `-issuer`.

## Sign-in and login

Upstream OpenRune has password login only (its token login is a TODO stub). Our fork, all live:

- **Server**: `server-token-auth` checks the client's token with Central over the world link (`central-token-login-op`,
  openruneCentral 2.0.3); `local-android-rsprot-token-gjstr` fixes the Android token decode.
- **Central, embedded in the server**: `central-game-session` (OIDC and game-session endpoints that mint the token),
  `central-sign-in-first-account` (a new name registers at sign-in), `central-embedded-jav-config` (a local jav_config, no
  Jagex hosts), `central-rights-test-mod` (fork-only test fix).
- **Sessions**: `server-reconnect` and `server-resumed-session-logout` (a resumed session's close removes the player).
- **Clients**: the LOCAL_AUTH APK signs in through Central (`client-android-central-sign-in`); desktops log in by a
  Central token, only Accept and Play (`h-desktops-token-login`); a relog after `::drop` and force-stop works
  (`client-resumed-session-relog`). Mobile login form typing was fixed today (`h-mobile-form-fields-filled`, 2890711).
- **Left**: the old `issuer.py` sidecar (`osrs-openrune-issuer`, `token-<slug>`) still runs; `h-ref-sign-in-no-issuer`
  removes it (stuck, see Do first).

## Upstream

- Card 9 (`goblin-367-rsprox-dump`, #367) published 18:01 UTC Nov 8; its comment answers only finding 6600852912
  (the user trimmed the extra replies; db1616e stops a card replying to findings already answered). A3 is proved by it.
- Card 12 (`hunter-feat-pr`, #408 at 637cedb) waits on the user. #408 is a draft; every card's last step readies a draft.
- Cards 4 (`central-token-login-op`) and 6 (`central-embedded-jav-config`): held by the Central upstream hold. Card 10
  (`server-reconnect`): held at the user's word. The user wants a PR's full body and `git diff origin/main...<head>`
  before approving.

## Awaiting the user

Card 12; question 17 (`h-pin-skip-cs2-spawn`: push fcb452014 to `fork/local/skip-cs2-packs` themselves, or let the next
run push that one pin ref); the Central and social holds; `hold: P2` in hd.yaml. Asks 1 and 2 show unanswered but their
changes are closed (`hd close`); they need nothing.

## Lessons from the last sessions

- An edit to this worktree is live at the orchestrator's next `hd`: replay old code against a snapshot before landing a
  decision change, not after.
- Derive a card's acts from its `steps_json`, never from the PR's wording.
- A landed row is void once a newer head of its change is submitted (M1, `Ledger.landed`); the same head after a failed
  gate is gated again (`store.regate_failed`).
- `hd answer` cannot close a change; the refusal prints the `hd close` line the user runs.
- Runs use at most 3 readers each (the user).
- A piped `track.sh up` needs `exec` for helpers (34aef53); a desktop's fixed-position click can hit a ban page's button,
  never press its top button; do not quote a success rate from a handful of starts.

## Rules that bind you

- CLAUDE.md "Rules" and "Shared rules" apply unchanged. Two public acts need the user; you never do either.
- A script of the checkout the loop runs from changes only by a ship (git replaces by rename): an in-place write to a
  running track script ends it with a syntax error.
- Keep the tree importable between commits; commit small with `hd commit <paths> -m "<message>"` (it holds
  `state/ship.lock`); run `python3 -m unittest discover -s tests` before each; check a touched doc's diagrams with
  `tests/mermaid_parse.mjs` (needs `npm i mermaid jsdom` in `~/.cache/mm`, `NODE_PATH=~/.cache/mm/node_modules`).
- An alert: fix it as your own commit and `hd dismiss <id>` naming it, or `hd new --from-alert <id>`. Never both.
- Don't repeat a run's work: read the ledger and message the orchestrator's session instead.
- No new concept, file, knob or special case without a PRD requirement; a mechanism you change is updated in
  ARCHITECTURE in the same commit. Decide on facts, never on elapsed time.

## Only the user decides

Every card; the Central upstream hold; the P3 band hold; the default decisions in docs/V9-PROPOSAL.md §5; when the
runtime move happens.

## The runtime move (the cutover's part 2)

At the user's desk, on their word: the session's `/exit`; stop `hd-loop.timer`; back up `state/hd.db` into
`~/osrs-harness/state/hd.db` with Python's `sqlite3` backup; `git -C ~/osrs-harness merge v9`; hd.yaml
`harness.base: refs/heads/main`, commit, push; copy `state/<slug>/`, `state/briefs/`, `state/live/` across; start
`harness/orchestrator.sh` from `~/osrs-harness`; then `git worktree remove` this worktree.

## Known gaps

- The `kpi` alert is not computed; `hd kpi` prints the metrics; the KPI table holds targets, not measurements.
- `publish.answered` reads the first 30 comments of a PR and assumes our latest comment answered every finding before it.
