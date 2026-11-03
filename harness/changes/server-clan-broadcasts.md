---
slug: server-clan-broadcasts
track: server
kind: change
title: 'Clans: clan broadcasts'
priority: P2
branch: content/server-clan-broadcasts
created: '2026-10-31T18:03:38Z'
deps:
- harness-no-powershell
- server-clan-guest
- harness-server-build-musicrepository
- harness-desktop-first-login
held: 'all: just push to fork, We will approve upstream PR for social features when more progress is complete.'
---
## Change
Split from server-clan-channels (the user, 2026-10-31: clans in five PRs, in order, each off upstream main: core with the settings interfaces, guest clans, broadcasts, Clan Hall). This PR: clan broadcasts, as on the OSRS wiki, built on the clans core. Draft spec: /home/alex/osrs-harness/evidence/server-clan-channels/accuracy.md. Cross-world clans are a stated caveat.

## Definition of done
- the gate passes; the review passes (scope, upstream style, PR text, in game on a branch server)
- mergeable as it stands; after the user's yes the PR leaves draft once upstream CI is green
