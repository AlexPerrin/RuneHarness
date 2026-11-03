---
slug: harness-token-issuer-long-term
track: harness
title: A long-term token issuer for the test stack
kind: change
priority: P0
deps:
- harness-desktop-token-login
created: '2026-11-01T10:08:58Z'
---
The user's word (on harness-desktop-token-login): A for now, consider a proper long-term solution. Today the test desktops get tokens from a separate issuer container (tools/server/token.py), while the user's earlier answer on server-token-auth said the auth sidecar would sign real JWTs; the sidecar image is in no carried tools repo and the live server uses it. Plan the long-term shape (one issuer for test and live, its source in a carried repo, how the client's LOCAL_AUTH provider and the server's token-login config point at it, how negative tokens are minted for QA), weigh it against the separate issuer, and file the changes it needs; the user decides before any live component changes.

The user's word (2026-11-01): "Token auth should mimic official as close as possible." So the token flow follows the official game's as observed (RSProx recordings of the Android/Jagex-account login, the client's own jav_config params 11/22 requests and the game-session token endpoint's request and response shapes): the same endpoints and fields, a token of the official length and character set inside the RSA login block, the same login packet and auth type 7, and the official login responses for a bad, expired or unknown token. Where our design differs from the observed official one (today's <account>.<expiry>.<HMAC> token is our own shape), the difference is named in evidence and closed, or named as unsourced where no recording shows it.
