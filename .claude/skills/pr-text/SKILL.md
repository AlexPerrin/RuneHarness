---
name: pr-text
description: "Judge a PR's or release's texts against its commit: every claim true of the exact head, upstream's template sections, one change, no deferral, the comment covering the net change. Judges the criteria claims, no-deferral, net-change and one-change; the scripted criterion texts checks the form."
---
# PR text (judgment; the form is a script)

Facts: `tracks/fork/server/text.py texts` checks the template sections, the `feat:`/`fix:` subject, no fork PR link, the
comment naming HEAD. Upstream's rules: CONTRIBUTING.md, `.github/pull_request_template.md`, AGENTS.md on upstream
`main`, whose blob shas the criteria record.

## claims
Every id, file, test name, result, "matches the wiki" tick and "verified in game" statement is true of the exact head:
check each against the diff, the test output and the accuracy spec. A ticked box that is not true fails the row.
## no-deferral
No Not-done list, no unticked item, no open question, nothing promised for a later PR: every reported defect is
fixed in this PR.
## net-change
On an existing PR, `pr-comment.md` covers exactly the commits the push carries since the PR's live head, no more.
## one-change
One quest, feature or fix; nothing unrelated; no open upstream PR for the same content; `Depends:` stated.
## tests
Every test file the diff adds is named in the text as the dupe test, the multi-case rule or the reviewer's request it
is; whether it is one is the code row `style` (`qa-server`), never fixed in the text.

A failed row of this skill is text only: qa fixes the text in the evidence dir and marks the row pass (no dev run).
