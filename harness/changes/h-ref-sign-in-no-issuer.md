---
slug: h-ref-sign-in-no-issuer
track: harness
priority: P0
deps:
- h-live-central-sign-in-deployed
- client-android-central-sign-in
---
# Desktops and the APK sign in through embedded Central: token-<slug> and osrs-openrune-issuer go

h-ref-embedded-central's sign-in half cannot run before central-game-session is live: tracks/fork/track.sh up token runs token-<slug> (issuer.py) unless SIGN_IN=central with a Central head that serves game-session (only the central track's up passes one), and the live stack's APK signs in at osrs-openrune-issuer (compose issuer, jav_config params 11, 20, 22, 28 naming port 8083). h-live-central-sign-in-deployed reapplies the desktops' live Central sign-in and client-android-central-sign-in moves the APK onto Central's endpoints; both wait on central-game-session (question 13). Needed once they are done: up token signs in through server-<slug>'s embedded Central by default (no token-<slug>; restart's in-memory session limit named), the deploy's APK jav_config names Central's sign-in instead of the issuer's port, compose and track.sh lose the issuer service, token-<slug> and issuer.py serve (issuer.py key stays only if the secret still comes from it). Done when a deploy and up token run no issuer container and a fresh C:\osrs-test desktop and the APK reach LOGGED_IN through Central's sign-in. Part of h-reference-deployment (PRD H8); found by run 229.
