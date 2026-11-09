# FileStore track

AlexPerrin/OpenRune-FileStore (of OpenRune/OpenRune-FileStore): the cache library (I/O, every config codec, gameval
references, packing). The game server and its cache tools consume it as the `dev.or2` artefacts (`all`, `filestore`,
`definition`, `filesystem`, `tools`) pinned in the fork's `gradle/libs.versions.toml` (`or2`); each module is named
as its artefact, so a FileStore head reaches the test server only inside a server image built with it (the fork's
build with `FILESTORE=<clone>:<commit>`, whose included build replaces the artefacts, transitively through the `all`
POM). The script is `tracks/filestore/track.sh <verb> <slug>` (verbs in its header); `hd` is the exact command the
brief names; the evidence dir is `evidence/<slug>/`.

## Branches
In the clone `origin` is upstream and `fork` the fork. `dev/<slug>` is the dev's ref, pushed to `fork` before
`hd submit`. Upstream has no PR CI: the gate is the head's own build and tests, and a server built with it.

## Rules for upstream (re-read the upstream README and any AGENTS.md or template on upstream `main` every run)
The same as the server track's: one change per PR, off current upstream `main`, never stacked; no deferral; new
commits on the PR branch, never a force-push; subjects `feat:`/`fix:`; no new KDoc or comments; a codec change
keeps every revision's module building.

## The dev
The brief names your clone (`~/src/OpenRune-FileStore/.worktrees/<slug>`, branch `dev/<slug>`). Commit;
`tracks/filestore/track.sh build <slug>` compiles your candidate in the build copy; `test <slug>` runs every
module's tests there; `up <slug> [N]` builds the fork's staging and Central's (the tree the test server runs) with your head
as its FileStore and starts that server with N logged-in desktops (one, the default, logged in by token); `log`, `down` as the fork's. A server change that needs your head names
your change in its `deps`: its candidate is then built with your head (composite), and its PR waits for yours to
merge and release. Write `pr-title.txt`, `pr-body.md`, `pr-comment.md` and `pr-reply-<id>.md` as the server track
does. Push `dev/<slug>` to `fork`, then `hd submit <slug>`.

## The reviewer
Judges from a server `up` built with the head (the cache it serves, the configs it decodes, the packs), every
criterion once, `hd verdict <slug> <head> rows.json`; a text-only failure is fixed in the evidence dir and marked pass.

## Never
Push any ref but yours; open or edit PRs; connect to Jagex; the live server; a process you did not start.

## Seed criteria
- claims | every PR claim, file and test name is true of the exact head | judge: pr-text | upstream
- no-deferral | no Not-done list, no unticked item, no open ask; every reported defect fixed in this PR | judge: pr-text | upstream
- one-change | one feature, nothing unrelated, no open upstream PR for the same content, Depends stated | judge: pr-text | upstream
- style | no added comments or KDoc, nothing public for a test | judge: qa-server | upstream
- serves | a server built with the head boots and serves its cache to a client | judge: qa-server | change
- tests | every module's tests pass at the candidate | script: bash $HD_ROOT/tracks/filestore/track.sh test
- evidence | pr-title.txt, pr-body.md, pr-comment.md present and non-empty | script: python3 $HD_ROOT/tracks/fork/server/text.py evidence | upstream
- subject | commit subjects start with feat: or fix:; no Claude-Session trailer; the co-author line only | script: python3 $HD_ROOT/tracks/fork/server/text.py commits | upstream
- texts | no fork PR link; pr-comment.md names HEAD | script: python3 $HD_ROOT/tracks/fork/server/text.py texts | upstream
