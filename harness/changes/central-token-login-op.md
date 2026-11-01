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

From central-token-login-op-3 (FAIL c2-checks, c3-session at 0485930ff): both rows required in-game proof through server-token-auth's build, which depends on this change, so they cannot pass before it ships. The code needs no fix; at the world link c2 (same fail codes as password LOGIN for ban, locked, reboot, world full, foreign character) and c3 (one session row, replaced on a second login, removed on LOGOUT) passed (evidence/central-token-login-op/qa3-worldlink-client.py). c2 and c3 are judged at the world link on this change; their in-game proof is server-token-auth's a4-central row.
