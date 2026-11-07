# Hand-off to the v9 harness dev

Current state as of 2026-11-07 18:00 UTC. The goal: a harness implemented and tested end to end against the workflow,
with the PRD validated. Check every fact here against `hd` and the ledger before acting on it.

## Do first

1. **The user runs `gh auth login -h github.com`.** The token in `~/.config/gh/hosts.yml` is invalid, so `track.sh gate` fails
   at `ci (remote:)`: `server-reconnect` (the head Android login needs) stopped there at 17:19 UTC, and brief 156 (goblin) is
   held on it. Nothing on the fork gets past its gate until this is done. It is the user's: ask, never work around it.
2. **After the login, runs 156 and 162 must not go to a dev.** Both gates recorded `ok=0` on the 401 before gate-ci held on one
   (52ae415), so `hd` still lists them. The fix is `hd stop 156`, `hd stop 162`, `hd regate goblin-367-rsprox-dump`, `hd regate
   server-reconnect`; the classifier denied these to the harness dev on 2026-11-07, so they wait on the user's word.
3. **Check the orchestrator supervises.** Session 18 started 17:19 UTC on the new definition (521aa15) and has been tested on
   no real case. Read what it does with brief 162, brief 156 and the open alerts (38, 41, 44, 45, 46, 48).

## Where things are

- **v9 runs from this worktree**, `~/osrs-harness/.worktrees/v9`, branch `v9`, pushed to `origin/v9`: `harness/orchestrator.sh` in
  the user's terminal (peer session `v9-09`, Sonnet 5.5; dev and qa on Opus 5.5; `agents: 5`), `hd-loop.timer`, `state/hd.db`.
  Commit here and push as you go. `~/osrs-harness` (`main`) is idle v8: its timer is off, its state is read-only context.
- **The user** runs a split terminal: the driver or this engineer session beside the orchestrator. This session is a one-off;
  the design is a manual driver and autonomous agents.
- The product repos: `~/osrs-plugins-reverse` (client), `~/src/OpenRune-Server` (fork), `~/src/OpenRune-Central-Server`,
  `~/src/OpenRune-FileStore`.

## Read, in this order

`docs/PROBLEM.md`, `docs/PRD.md` (the requirements, each naming its mechanism), `docs/ARCHITECTURE.md`, then
`docs/ACCEPTANCE.json` (the proof of each). `docs/V9-PROPOSAL.md` and `docs/V9-BRIEF.md` hold the v8 context.
`docs/ISSUES.md` does not exist: it is created when a root cause is too large for its run.

## The test server

Live is `9bb231f632e1_cc6e461efc74e` (staging, deployed 07:39 UTC), ports 43594 and the sidecars issuer, http and http-desktop.
The cutover's part 1 is done: the key pair and `tree.json` are in `state/live/`, and `server-token-auth`, `local-android-rsprot-token-gjstr`
and `local-cs2-group-names` are live. `state/live/` here is what the running stack uses.

## Android login, the user's first priority

**A mobile has reached LOGGED_IN on live, but unreliably:** 4 of 6 starts, then 0 of 4 (run 146), then 0 of 5. Each cause so far:

| symptom | cause | state |
|---|---|---|
| "the app died" 16 s after start | 15 clientscript groups with name hash 0: the app's by-name read of `version.dat` reads null | fixed, live: `local-cs2-group-names`. Dropped by the cutover when the server version moved to FileStore; drop this carry when `filestore-cs2-group-name-hash` lands |
| unknown window: the launcher | the process runs before its window takes focus | fixed, 59f25f6 |
| LoginIndex 9 | the connection drops as a first LOADING ends, the client reconnects, `ConnectionHandler.onReconnect` is a TODO answering ConnectFail (run 155, its own finding, unverified) | `server-reconnect` submitted abb8662, gate failing on the token |
| LoginIndex 39 | the client's error page, default text "Connection failed during login request"; run 154: the issuer closing after the body | 40e9fe3 live on the issuer since 17:49 UTC, not yet measured on a start. All issuer requests logged 200 on the failure |
| the start error page (raw game state 1000, logged as UNKNOWN) | filed by run 157 | `client-host-raw-gamestate` (listed; run 159 wedged and was stopped), then `h-mobile-login-start-error` (submitted 7303903, dep) |
| measure: "System UI isn't responding" | not traced; it dialogs on the mobile as an unknown window | open |
| three of my starts ended at 222 s with no result | not traced | open |

`client-probe-no-stop` depends on the mobile chain, then ships and lets `client-api` land a value; the measure has stopped at
3 starts and restarts at the next harness ship. A logged-in phone later dropped to "You were disconnected" or "Connecting to
server...", about 5 minutes after login on the one timed; not traced. Quest Helper logs an NPE at login (`Cheerer.zoinkwizOutfit`),
harmless so far. The user's "Blocked for Suspicious login" in the game client: most likely run 145's deliberate lock test
on a throwaway account (client text "locked due to suspicious activity"), unconfirmed; live has no punishments.

## The chains

- **Central and FileStore** (the user: Central auth could replace client scripting): `central-embedded-jav-config` →
  `h-central-up-sign-in` → `central-game-session` → `h-desktops-token-login` → `h-reference-deployment` (PRD H8: the local stack as a
  reference OpenRune deployment; each deviation named in ARCHITECTURE). FileStore (`h-filestore-up-login`,
  `filestore-cs2-group-name-hash`) waits on token login.
- `server-token-auth` is live on staging; its upstream path waits on `central-token-login-op` landing on main (card 4 held).
- **Priority** (the user): client first with the server work it needs, then overlapping upstream work, then content for its
  own sake (17 quest changes held at P4). Agents limited to 5.

## ACCEPTANCE

31 requirements, 3 with a `pending:` proof: **H8** (above), **A2** (a killed publish resuming: test on a lab card), **A3** (a maintainer
finding answered through the loop). Replace each `pending:` with the observed fact; recount before quoting a figure.

## This session's lessons

- The orchestrator now supervises by judgment: `hd` gives it a `live` line per run and the alerts. When supervision fails, widen
  what it sees and may judge; don't add a threshold. A wedge cost 7 hours overnight (host awake: no Windows sleep events).
- A piped `track.sh up` never returned because a helper shell held the caller's stdout (34aef53, `exec`). Any script that
  starts a long-lived process from a pipe can repeat this.
- Moving a fix between repos can drop it from the stack: check that the tree about to deploy keeps every behaviour it replaces.
- A judge of a change that needs a live deploy cannot prove it before the deploy: the proof belongs after it.
- A desktop's fixed-position click can hit a ban or lock page's button, which opens runescape.com (browser blocked at the JVM,
  4e656d7). Never click or press Enter on those pages' top button.
- Do not quote a success rate from a handful of starts.

## Rules that bind you

- CLAUDE.md "Rules" and "Shared rules" apply unchanged. Two public acts need the user; you never do either.
- `~/osrs-harness` (branch `main`) is idle v8 until the runtime move below: never write there.
- A script of the checkout the loop runs from changes only by a ship (git replaces a file by rename, so a running bash
  keeps the old one): an in-place write to a running track script moves it under bash and ends it with a syntax error.
- The orchestrator session runs this worktree's working copy: every saved edit is live at its next `hd`. Keep the tree
  importable between commits; commit small; the replay compares a candidate with its merge base, so your own commits
  do not fail others' gates.
- The shell of a session resets its cwd to `~/osrs-harness` (the live checkout) after a command that ends elsewhere:
  use absolute paths into this worktree; never write under `~/osrs-harness`.
- Claude Code snapshots hook matchers at session start: a hook change is tested by a fresh session (the orchestrator
  restarts itself on a moved definition; a hook change needs `hd restart` by hand).
- The orchestrator acts on alerts. In an engineering session you fix one at once as your own commit and `hd dismiss <id>`
  naming it, or file it with `hd new --from-alert <id>`. Never both.
- Don't repeat a run's work: read the ledger and message `v9-09` (the orchestrator's session) rather than running a
  change's fix beside its run. A proof of your own uses a slug no run holds (`client-api` for `track.sh up`), and a piped
  `up` needs `34aef53` or later.
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

- The default decisions in docs/V9-PROPOSAL.md §5, and when the runtime move happens.
- The Central upstream hold, the P3 band hold (`hold: P2` in hd.yaml), and every card.

## The runtime move (the cutover's part 2)

At the user's desk, on their word, once Android logs in reliably: the session's `/exit`; stop `hd-loop.timer`; back up
`state/hd.db` into `~/osrs-harness/state/hd.db` with Python's `sqlite3` backup (no `sqlite3` CLI here); `git -C ~/osrs-harness merge v9`; hd.yaml
`harness.base: refs/heads/main`, commit, push; copy `state/<slug>/`, `state/briefs/`, `state/live/` across; start
`harness/orchestrator.sh` from `~/osrs-harness`; then `git worktree remove` this worktree.

## Awaiting the user

`gh auth login`; the word on step 2; Hunter #408 question 4; the triage of comments on #354 and #367; the `hd park` proposal; lab cards 2 and 3.

## Known gaps

- The `kpi` alert is not computed; `hd kpi` prints the metrics. Every number in the KPI table is a target, not a measurement.
- The image rebuild churn (one image released three times, rebuilt) is untraced.
- `tests/mermaid_parse.mjs` needs `npm i mermaid jsdom` in `~/.cache/mm` (its header); run it with `NODE_PATH=~/.cache/mm/node_modules`.
- The `devtools` repo (OpenRune-Developer-Tools) is in ARCHITECTURE §11 but not in `hd.yaml`; its fork does not exist yet.
