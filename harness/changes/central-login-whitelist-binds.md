---
slug: central-login-whitelist-binds
track: central
title: Login restrictions no longer close the world link
kind: change
priority: P2
deps: []
created: '2026-11-01T04:27:39Z'
---
Found by central-token-login-op-3 at the world link: on any world with login restrictions enabled, Central closes the connection on LOGIN (and the new token LOGIN). Cause: game/world/login_whitelist_exists.sql has 2 placeholders but the code binds only 1. Upstream bug, not caused by central-token-login-op. Fix: bind what the query needs so a whitelisted account logs in and a non-whitelisted one gets the restriction's reply. Upstreamable: the PR to OpenRune/OpenRune-Central-Server needs the user's yes on a card.
