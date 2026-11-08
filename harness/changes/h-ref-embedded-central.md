---
slug: h-ref-embedded-central
track: harness
priority: P0
deps:
- central-embedded-jav-config
- h-desktops-token-login
- h-ref-server-bundle
- h-ref-sign-in-no-issuer
- h-ref-up-central-jav-config
---
# up, live-desktop and the deploy take jav_config and sign-in from embedded Central on upstream's ports

game.example.yml's central.same-instance: true (link 9091, http 9090): tracks/fork/track.sh up, live-desktop and the deploy serve jav_config.ws (the local template through OPENRUNE_JAV_CONFIG_URL_TEMPLATE=file://, never client.blurite.io: Privacy) and the sign-in from the game's embedded Central, and run no token/issuer, http-<slug> nor osrs-openrune-http-desktop container; compose and track.sh lose them. Done when javcheck.py passes on Central's own /jav_config.ws for up and the deploy, and a fresh C:\osrs-test desktop and the APK reach LOGGED_IN with those containers gone. Upstream blob shas: evidence/h-reference-deployment/upstream-shas.md (re-check before acting). Part of h-reference-deployment (PRD H8).
