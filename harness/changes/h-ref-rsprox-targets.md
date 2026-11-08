---
slug: h-ref-rsprox-targets
track: harness
priority: P0
deps:
- h-ref-embedded-central
---
# Desktops connect through RSProx's proxy-targets as upstream's README says

OpenRune-Server README Client Setup: the client connects through RSProx with a proxy-targets entry (jav_config_url = embedded Central's /jav_config.ws, revision, modulus from .data/client.key). up and live-desktop write that entry and launch the desktop through RSProx instead of pointing OPENRUNE_ENDPOINT at the server; the existing RSProx recording use keeps working. Done when a fresh desktop reaches LOGGED_IN through RSProx on up and on the deploy. Upstream blob shas: evidence/h-reference-deployment/upstream-shas.md (re-check before acting). Part of h-reference-deployment (PRD H8).
