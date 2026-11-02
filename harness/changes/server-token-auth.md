---
slug: server-token-auth
track: server
title: Token login for the Android app, verified like the official flow
kind: change
priority: P1
deps:
- harness-deploy-survives-tools-ship
- central-token-login-op
- harness-central-include-app
- harness-desktop-token-login
- harness-test-central-include
- harness-gate-ci-central-dep
created: '2026-11-01T03:23:48Z'
---
The user's word (2026-11-01): real token auth, so mobile login is 1:1 with official. Upstream OpenRune-Server main supports only password login: rsprot ConnectionHandler.onLogin sends TokenAuthentication to tokenLogin, a TODO stub that returns InvalidLoginPacket. The official Android app signs in with a Jagex account (AppAuth OpenID token), then sends a token login (auth type 2, as rsprot GameLoginDecoder decodes it). The fork pin local/local-auth (a8cae0979) is a spike that never verifies the token and gives every account the fixed password android-local. Implement token login properly: the local OpenID provider issues tokens for an account, and the server verifies the token (signature, expiry, audience) and maps it to that account through OpenRune Central, with the same responses as passLogin for an invalid or expired token. Accuracy: the login responses and flow must match the official server's (RSProx recordings and the wiki first). This is upstreamable: the PR to OpenRune needs the user's yes on a card. When it lands, local/local-auth leaves the pins (the user's pin list) and the client's LOCAL_AUTH provider points at the real token issuer. Evidence: a read-only lookup of upstream auth on 2026-11-01 (ConnectionHandler.kt, AccountLoadResponseHook.kt, OpenRuneCentralWorldLink).

From central-token-login-op-5: central-token-login-op's c2-checks and c3-session are judged at the world link; their in-game proof is this change's a4-central row. That row names registration, logout and the friends list but no fail code, so no row proves in game that a token login of a banned (or locked) account gets the official banned (locked) response. a4-central covers it.

The user's word (2026-11-01, on harness-desktop-token-login): the token is a compact signed token of 90 bytes or less (option A), because the official client carries it in its RSA login block, which fits about 90 bytes; an RS256 JWT does not fit and the login RSA keys stay as they are. The server verifies that compact token (signature, expiry, the account it names) with the same responses as passLogin for an invalid or expired one. The agreed contract's JWT rows (signature, issuer, audience, expiry) are re-agreed for the compact format.

The user's word (2026-11-01): "Token auth should mimic official as close as possible." So the token flow follows the official game's as observed (RSProx recordings of the Android/Jagex-account login, the client's own jav_config params 11/22 requests and the game-session token endpoint's request and response shapes): the same endpoints and fields, a token of the official length and character set inside the RSA login block, the same login packet and auth type 2, and the official login responses for a bad, expired or unknown token. Where our design differs from the observed official one (today's <account>.<expiry>.<HMAC> token is our own shape), the difference is named in evidence and closed, or named as unsourced where no recording shows it.
