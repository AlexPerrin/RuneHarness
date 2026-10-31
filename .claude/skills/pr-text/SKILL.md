---
name: pr-text
description: "Judge a PR's or release's texts against its commit: every claim true of the exact head, upstream's template sections, one change, no deferral, the comment covering the net change. Judges the contract rows claims, no-deferral, net-change and one-change; the script row texts checks the form."
---
# PR text (judgment; the form is a script)

Facts: `tracks/server/text.py texts` checks the template sections, the `feat:`/`fix:` subject, no fork PR link, the
comment naming HEAD. Upstream's rules: CONTRIBUTING.md, `.github/pull_request_template.md`, AGENTS.md on upstream
`main`, whose blob shas the contract records.

## claims
Every id, file, test name, result, "matches the wiki" tick and "verified in game" statement is true of the exact head:
check each against the diff, the test output and the accuracy spec. A ticked box that is not true fails the row.
## no-deferral (v7 cause: 10 findings; a maintainer's "I'd like the cutscene too" became 23 runs)
No Not-done list, no unticked item, no open question, nothing promised for a later PR: every reported defect is
fixed in this PR.
## net-change (8 findings)
On an existing PR, `pr-comment.md` covers exactly the commits the push carries since the PR's live head, no more.
## one-change
One quest, feature or fix; nothing unrelated; no open upstream PR for the same content; `Depends:` stated.
## tests (hard)
Every test file and method the diff adds is justified in the text as a rule with several cases, a reviewer's request
or a dupe test; otherwise the row fails and the test leaves the PR.

A failed row of this skill is text only: qa fixes the text in the evidence dir and marks the row pass (no dev run).
