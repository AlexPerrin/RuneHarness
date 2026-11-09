# Central track

AlexPerrin/OpenRune-Central-Server (of OpenRune/OpenRune-Central-Server): accounts, sessions, world-link auth,
`jav_config.ws`, `worldslist.ws`. The game server runs Central in-process (`central.same-instance: true` in
game.yml) and consumes it as the Maven artefacts `dev.or2:central-common`, `central-worldlink` and
`openrune-central` pinned in the fork's `gradle/libs.versions.toml` (`openruneCentral`). A Central head reaches the
test server only inside a server image built with it (the fork's build with `CENTRAL=<clone>:<commit>`, which
substitutes the three artefacts with the head's projects). The script is `tracks/central/track.sh <verb> <slug>`
(verbs in its header); `hd` is the exact command the brief names; the evidence dir is `evidence/<slug>/`.

## Branches
In the clone `origin` is upstream and `fork` the fork. `dev/<slug>` is the dev's ref, pushed to `fork` before
`hd submit`. Upstream has no PR CI (a release workflow on tags only): the gate is the head's own test run.

## Rules for upstream (re-read the upstream README and any AGENTS.md or template on upstream `main` every run)
The same as the server track's: one change per PR, off current upstream `main`, never stacked; no deferral; new
commits on the PR branch, never a force-push; subjects `feat:`/`fix:`; no new KDoc or comments; config keys in
`CentralConfig.kt` with a YAML path and an env alias; the config example kept current. Central PRs are held from
upstream until the user lifts the hold (hd.yaml, ARCHITECTURE §11).

## The dev
The brief names your clone (`~/src/OpenRune-Central-Server/.worktrees/<slug>`, branch `dev/<slug>`). Commit;
`tracks/central/track.sh build <slug>` compiles your candidate in the build copy; `test <slug>` runs every module's
tests there; `up <slug> [N]` builds the fork's base with your head as its Central and starts that server with N
logged-in desktops (the fork's `up`: a head whose embedded Central reads no `file://` jav_config is merged with Central's
staging first, so the server's own Central serves the desktops' `jav_config.ws`); every up signs its desktops in through your Central's sign-in (a head without it is merged with Central's staging first); `log`, `down` as the fork's. A server change that needs your head names your
change in its `deps`: its candidate is then built with your head (composite), and its PR waits for yours to merge and
release. Write `pr-title.txt`, `pr-body.md`, `pr-comment.md` and `pr-reply-<id>.md` as the server track does. Push
`dev/<slug>` to `fork`, then `hd submit <slug>`.

## The reviewer
Judges from a server `up` built with the head (the login flow, sessions, the world link, `jav_config.ws`), every
criterion once, `hd verdict <slug> <head> rows.json`; a text-only failure is fixed in the evidence dir and marked pass.

## Never
Push any ref but yours; open or edit PRs; connect to Jagex; the live server; a process you did not start.

## Seed criteria
- claims | every PR claim, file and test name is true of the exact head | judge: pr-text | upstream
- no-deferral | no Not-done list, no unticked item, no open ask; every reported defect fixed in this PR | judge: pr-text | upstream
- one-change | one feature, nothing unrelated, no open upstream PR for the same content, Depends stated | judge: pr-text | upstream
- style | no added comments or KDoc, nothing public for a test, config keys with an env alias and an example | judge: qa-server | upstream
- login | the login, session and world-link flows work from a server built with the head | judge: qa-server | change
- tests | every module's tests pass at the candidate | script: bash $HD_ROOT/tracks/central/track.sh test
- evidence | pr-title.txt, pr-body.md, pr-comment.md present and non-empty | script: python3 $HD_ROOT/tracks/fork/server/text.py evidence | upstream
- subject | commit subjects start with feat: or fix:; no Claude-Session trailer; the co-author line only | script: python3 $HD_ROOT/tracks/fork/server/text.py commits | upstream
- texts | no fork PR link; pr-comment.md names HEAD | script: python3 $HD_ROOT/tracks/fork/server/text.py texts | upstream
