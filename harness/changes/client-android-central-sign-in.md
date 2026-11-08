---
slug: client-android-central-sign-in
track: client
priority: P0
deps:
- central-game-session
- h-live-apk-central-sign-in
---
# The official Android app signs in through Central's endpoints on the live stack

Once central-game-session is live (with h-live-central-sign-in): the LOCAL_AUTH APK on the live stack signs in through Central's discovery, oauth2/auth, oauth2/token, game-session sessions, accounts and tokens endpoints and logs in as the signed-in account, first packets and welcome as 20261016T082141-scrubbed.txt tick 0. This is central-game-session's G11 (evidence/central-game-session/accuracy.md), moved here because only a deploy can show it (PRD G1). Fix wherever it fails: a refusal in Central is a central change with the repro.
