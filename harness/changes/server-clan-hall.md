---
slug: server-clan-hall
track: server
kind: change
title: 'Clans: Clan Hall, coffer, vexillum, cloak, events and recruitment board'
priority: P3
created: '2026-10-31T18:03:38Z'
deps: [harness-no-powershell, server-clan-broadcasts]
---
## Change
Split from server-clan-channels (the user, 2026-10-31: clans in five PRs, in order, each off upstream main: core with the settings interfaces, guest clans, broadcasts, Clan Hall). This PR: Clan Hall, coffer, vexillum, cloak, events and recruitment board, as on the OSRS wiki, built on the clans core. Draft spec: /home/alex/osrs-harness/evidence/server-clan-channels/accuracy.md. Cross-world clans are a stated caveat.

## Definition of done
- the gate passes; the review passes (scope, upstream style, PR text, in game on a branch server)
- mergeable as it stands; after the user's yes the PR leaves draft once upstream CI is green
