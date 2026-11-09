# PR lab track

AlexPerrin/pr-lab is a repo of our own that is its own upstream: the loop's GitHub paths (a PR opened, CI read, a comment
posted, ready, a second head, a merge landing the change) run against it with no maintainer involved. Changes here are
tests of the harness, named `lab-*`; a definition says exactly what to commit, nothing more. The clone is `~/src/pr-lab`
(`origin` is both the fork and upstream); the dev ref is `dev/<slug>`, pushed to origin before `hd submit`. CI
(`.github/workflows/check.yml`) fails when a file named `FAIL` exists at the repo root: a change that wants CI red commits one.
No build, no server, no game, no skills.

## Texts
`evidence/<slug>/pr-title.txt` (one line), `pr-body.md` and `pr-comment.md` (plain text, a line each is enough;
pr-comment.md names the head). No template.

## Criteria run
The seeds below are the criteria; add none. Hand back `criteria agreed`.

## Seed criteria
- texts | pr-title.txt, pr-body.md and pr-comment.md exist and are non-empty in the evidence dir | script: test -s "$EVIDENCE/pr-title.txt" && test -s "$EVIDENCE/pr-body.md" && test -s "$EVIDENCE/pr-comment.md" | upstream
