---
slug: lab-ci-red
track: lab
priority: P1
pr: 2
public: content/lab-ci-red
---
# lab: a head whose CI fails, then a second head that passes (the publish's CI step lists the dev; the second card edits and comments)

A test of the loop's CI-failure path on the PR lab (tracks/lab/track.md); the lab's CI fails when a file named FAIL exists at the repo root. First round, on dev/lab-ci-red (clone ~/src/pr-lab, pushed to origin before hd submit): add the file FAIL with the line 'the lab's CI fails on this file' and append 'ci red test' to README.md; texts in evidence/lab-ci-red/ as in lab-hello (pr-title.txt 'lab: ci red test', pr-body.md one line, pr-comment.md naming the head). hd submit. When a later brief says CI failed at your head: remove FAIL (git rm), commit, push, hd submit again; the second head's CI is green. Nothing else.
