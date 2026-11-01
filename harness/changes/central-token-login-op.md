---
slug: central-token-login-op
track: central
title: Token LOGIN op on the Central world link
kind: change
priority: P0
deps:
- harness-central-track
created: '2026-11-01T04:04:00Z'
---
server-token-auth (contract agreed, evidence/server-token-auth/contract.md rows one-change and a4-central) needs OpenRune-Central-Server to map a verified token to its account: a token LOGIN op on the world link, the Central PR of the user's choice (a Central PR plus a server PR). The server PR declares Depends: on this PR and the matching Central dependency version; no Central or sidecar code goes in the server head. Accuracy as server-token-auth: responses match the official login flow. Upstreamable: the PR to OpenRune/OpenRune-Central-Server needs the user's yes on a card.
