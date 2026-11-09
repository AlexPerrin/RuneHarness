# Server track (the fork)

The fork AlexPerrin/OpenRune-Server (of OpenRune/OpenRune-Server) is the test server; a checked change reaches it on
`staging` and, independently, upstream as a PR after the user's yes. The script is `tracks/fork/track.sh <verb> <slug>`
(verbs in its header); `hd` is the exact command the brief names; the evidence dir is `evidence/<slug>/`.

## Branches on the fork
In the clone `origin` is upstream and `fork` the fork. `fork/main` mirrors upstream. `dev/<slug>` is the dev's ref, the
only one a dev pushes; the change's head is its tip on the fork. `content/<slug>` and `fix/<slug>` are the public PR
branches, moved only by a publish after the user's yes. `local/*` are test-only pieces that never go upstream.
`gate/<slug>` holds the gate's CI commit. `staging` holds upstream `main`, the pins and every checked head, merged
once each; the live test server runs it.

## Rules for upstream (re-read AGENTS.md, CONTRIBUTING.md and the PR template on upstream `main` every run; the criteria record their blob shas)
- One change per PR: one quest, feature or fix, off current upstream `main`, never stacked, no commit of another
  open PR. Shared code is its own change that merges first; dependencies are `Depends:` in the PR text.
- Check upstream first (gh pr list on OpenRune/OpenRune-Server with --search, and the issues). Theirs wins.
- A PR is ready only when every reported defect is fixed in it; nothing is promised for a later PR, no Not-done list,
  no unticked checklist item.
- Updates are new commits on the PR branch (merge `main` in, never force-push); the description is never replaced.
- Default no tests, except a dupe test per item-moving flow (below), a rule with several input cases, or a test a
  reviewer asked for, each named so in the PR text; never a test of an interaction, a dialogue, quest stages or a
  script's flow (qa fails `style` on it). No new KDoc or explanatory comments. Nothing public for a test. Toggles in
  the config with a default. Subjects `feat:`/`fix:`. State in varbits and varps; gameval symbols, never raw ids;
  game data in the cache, not in Kotlin. A difference from the official game is fixed, never recorded as a quirk;
  one the server cannot fix is `hd ask`.
- Upstream texts never link a fork PR (`AlexPerrin/OpenRune-Server#N`, `.../pull/N`); naming the fork is fine. Never
  open a PR, issue or comment on the fork.

## Accuracy (the spec `evidence/<slug>/accuracy.md`, written in the criteria run, checked by dev and qa)
Sources in order: RSProx recordings of the official game and the OSRS wiki (with the cache and Mod posts) together;
where they disagree cite both and follow the newer; LostCity and other reference implementations only as evidence for
a guess, never a source. Look up with the `osrs-mcp` tools. Recordings may hold other players' names and chat: never
commit, quote or upload them; cite recording ids and packets. Per mechanic: its source, the behaviour, what the
recording shows (anims, spot anims, sounds, messages, dialogue order, varps per stage, interfaces, tick timings).
A claim of "no recording" is made only after `tracks/fork/track.sh recordings <slug> <packet|text>` searched the index.
A rule the wiki names but no cache, recording or transcript bounds is a reconstruction: implement the best one and
name it in the PR notes as unsourced. Each rule is one criterion: `hd criterion add <slug> acc-<n> --kind judge
--text "<rule>" --cmd accuracy --source accuracy`.

## Gameval ids
Use the official id when the cache has one (`gameval_search`). For new state write `name = -1`, run
`tracks/fork/server/gamevals.py assign <clone>` (the highest id free in upstream main, every pin of hd.yaml and every
open dev head) and push at once. The gate runs `gamevals.py check`: of two branches holding one id under two names,
the later taker renumbers.

## Dupe tests (upstream AGENTS.md "Unit tests")
Every flow that moves items (`inv*` of `api/invtx` and `ProtectedAccess`, `wornUnequip`, `objRepo.add/del`, shop ops)
has one test class in the module's `src/test/kotlin`, built like `FoundryRewardTransactionsTest.kt` or
`BullBonesTest.kt`, covering no space, overflow at `Int.MAX_VALUE`, repeats and races, and accounting of every obj's
total. A path that cannot occur is one plain line in the PR notes. QA tries each flow in game: full inventory, fast
repeat, source removed mid-action, counts read with `get_inventory` and `get_container_history`.

## The dev
The brief names your clone (`~/src/OpenRune-Server/.worktrees/<slug>`, branch `dev/<slug>`). Commit;
`tracks/fork/track.sh build <slug>` builds your working copy's candidate in the build copy: your head merged onto
staging (what the test server runs: the pins, token login, every staged head), while the branch itself stays on
upstream main and never takes staging in (its PR holds no other change; the fork CI runs it on main alone); a head
that does not merge onto staging is yours to make merge. `up <slug> [N]` starts the server from that build with N
desktops logged in by token through the server's own Central sign-in (Play alone, each its own account) and prints their devtools ports (the server's own Central serves
their `jav_config.ws` from a file: a build whose Central reads none, the published one, is first rebuilt with Central's
staging, the Central the test server runs); `test <slug> [module...]` builds,
then runs each module's tests, its integration tests and spotlessCheck on the build copy (no module: every module the
change touches) and writes `evidence/<slug>/test.log`; never gradle by hand. `log <slug> <pattern>` reads the server
log; `restart <slug>` is a down and a `RESUME=1` up with the same desktops, staff and quest mode (Central keeps sign-in sessions
in memory): the database kept, each desktop a new instance, so read its devtools ports again from its output. Each up
starts a fresh database; `RESUME=1 … up` starts from the accounts as the change's last `down` saved them. The realm is
live's (`dev_mode` off, xp at 1x) and every desktop's account a member at rank 0; `STAFF=<N>[,<M>...]` on one `up`
makes those desktops' accounts administrators. `live-desktop <slug>` signs one desktop in through the live Central as the slug's own account, by token.
The server `up` starts runs game.yml with `quest-requirements` `mode` from the front matter `quest-mode:`
(`respect-progress` by default, or `assume-completed`); `QUEST_MODE=<mode>` on one `up` overrides it; PR notes name
it as the verification setting. Every server run goes through track.sh, never a container by hand. Test through
`osrs-devtools-desktop` data tools; a screenshot only for how something is drawn. Write `pr-title.txt`, `pr-body.md`
(on an open PR they replace the live ones that differ), `pr-comment.md` (the push summary: names the head and every
commit the push carries since the PR's live head, no quote, no @) and, for each finding answered, `pr-reply-<finding
id>.md` (the reply alone: the finding quoted with `> `, @ only its author). Run the scripted criteria yourself
(`tracks/fork/track.sh test <slug>`, `spotless`), push `dev/<slug>` to `fork`, then `hd submit <slug>`. `hd ask
<slug> "..."` when a decision is not yours; `hd show <slug>` first, always.

The desktops are Windows programs run from bash through WSL interop (`WINDOWS_SYSTEM32`, default
`/mnt/c/Windows/System32`; `DESKTOP_DIR`, default `/mnt/c/osrs-test`: the template, its JDK, RSProx launcher and
staged home), rebuilt by `server/desktop_template.sh` when an up finds it gone. Each up creates the desktops it needs (instance N is `DESKTOP_DIR/run/N`, devtools port 7779+N, owned
by the up's slug); only a JVM carrying `-Dosrstest.marker=osrs-test-runN` is ever stopped, never the user's own
RuneLite. The stack's record is `state/<slug>/up.json`, mirrored into the ledger's `stack` row; `down` removes what
it names. Each desktop's devtools endpoint answers only a request carrying the up's bearer token. Windows processes a
run starts are recorded under the run's scope (`state/winpids/`), which `hd stop` ends with the run.

## The reviewer
Never writes the code it checks. Judges every criterion from the same build (`tracks/fork/track.sh up <slug>`), in
game for every player-facing claim, and records `hd verdict <slug> <head> rows.json` with every criterion pass or fail
and a note per failure. A text-only failure (PR title, body, comment): fix the text in the evidence dir and mark it
pass. A difference from the official game is a failed criterion, never a caveat. Only the user's answer accepts a
difference. A failing note's remedy agrees with the source it cites.

## Never
Touch a mobile or the tester account's items (keep its GE lobster offer, drop only what you spawned); restart the
live server (`osrs-openrune*`); push any ref but yours; open or edit PRs; connect to Jagex; read `C:\Users\Alex\.runelite`;
stop a process you did not start; use the DB tool for writes.

## Seed criteria
A judged criterion names the skill that judges it; `upstream` marks one that applies only to a change that opens a PR.
Scripted criteria run with SLUG, HEAD, T, TCOMMIT, BASE, CLONE, BUILD, EVIDENCE, PR, PUBLIC_BRANCH in the env, cwd the build copy.
- claims | every PR claim, id, file, test name and ticked box is true of the exact head | judge: pr-text
- rsprox | timings, steps and messages checked against RSProx recordings tick by tick before the wiki | judge: accuracy
- no-deferral | no Not-done list, no unticked item, no open ask; every reported defect fixed in this PR | judge: pr-text | upstream
- net-change | on an existing PR, pr-comment.md covers only the commits since the PR's live head | judge: pr-text | upstream
- unsourced | the PR notes name every reconstruction and every cheat used to verify | judge: accuracy
- no-raw-data | no game data or raw ids in Kotlin; gameval symbols; state in varbits and varps | judge: qa-server
- playable | every flow playable without a cheat; in-game evidence in the evidence dir | judge: qa-server
- one-change | one feature, nothing unrelated, no open upstream PR for the same content, Depends stated | judge: pr-text | upstream
- style | no added comments or KDoc, no test but a dupe test, a multi-case rule or a reviewer's request, nothing public for a test, no quirk entries | judge: qa-server
- dupes | each item-moving flow's four paths tested with totals, or a reason that holds | judge: dupes
- accuracy | each rule of accuracy.md matches in game; a difference no answer of the user accepts fails it | judge: accuracy
- evidence | accuracy.md, pr-title.txt, pr-body.md, pr-comment.md present and non-empty | script: python3 $HD_ROOT/tracks/fork/server/text.py evidence | upstream
- subject | commit subjects (on an existing PR, those after its live head) start with feat: or fix:; no Claude-Session trailer; the co-author line only | script: python3 $HD_ROOT/tracks/fork/server/text.py commits | upstream
- texts | template sections present; no fork PR link; pr-comment.md names HEAD | script: python3 $HD_ROOT/tracks/fork/server/text.py texts | upstream
- gamevals | custom gameval ids unique across upstream main, the pins and open dev heads | script: python3 $HD_ROOT/tracks/fork/server/gamevals.py check
- dupe-tests | every module whose main sources gain an item-moving call has a test source added or changed | script: python3 $HD_ROOT/tracks/fork/server/text.py dupes
- spotless | spotlessCheck passes on every module the head changes from main | script: bash $HD_ROOT/tracks/fork/track.sh spotless
- ci | fork CI and Formatting green on gate/<slug> at the candidate | script: bash $HD_ROOT/tracks/fork/track.sh gate-ci | upstream

Login refusal pages: never click or press Enter on a ban or lock page's top button (View Appeal Options, Recover Account). It opens runescape.com in the user's browser. Leave by Back, read from the screenshot, and prove a refusal from the server's log and the page text.
