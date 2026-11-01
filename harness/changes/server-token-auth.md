---
slug: server-token-auth
track: server
title: Token login for the Android app, verified like the official flow
kind: change
priority: P0
deps: []
created: '2026-11-01T03:23:48Z'
---
The user's word (2026-11-01): real token auth, so mobile login is 1:1 with official. Upstream OpenRune-Server main supports only password login: rsprot ConnectionHandler.onLogin sends TokenAuthentication to tokenLogin, a TODO stub that returns InvalidLoginPacket. The official Android app signs in with a Jagex account (AppAuth OpenID token), then sends a token login (auth type 7). The fork pin local/local-auth (a8cae0979) is a spike that never verifies the token and gives every account the fixed password android-local. Implement token login properly: the local OpenID provider issues tokens for an account, and the server verifies the token (signature, expiry, audience) and maps it to that account through OpenRune Central, with the same responses as passLogin for an invalid or expired token. Accuracy: the login responses and flow must match the official server's (RSProx recordings and the wiki first). This is upstreamable: the PR to OpenRune needs the user's yes on a card. When it lands, local/local-auth leaves the pins (the user's pin list) and the client's LOCAL_AUTH provider points at the real token issuer. Evidence: a read-only lookup of upstream auth on 2026-11-01 (ConnectionHandler.kt, AccountLoadResponseHook.kt, OpenRuneCentralWorldLink).
