---
slug: h-ref-apk-jav-config-central
track: harness
priority: P0
deps:
- h-ref-rsprox-targets
---
# The APK takes jav_config.ws and slr.ws from embedded Central: the osrs-openrune-http sidecar goes

The last container H8 names still running after the h-ref chain (sign-in-no-issuer, embedded-central, rsprox-targets): at harness/h-ref-rsprox-targets (ee98d5e) tracks/fork/server/docker-compose.yml keeps service http (osrs-openrune-http, image osrs-rsps-test:241, host 8081:8080, WORLD_HOST 10.0.2.2) serving the APK's jav_config.ws (template params 11, 20, 22, 28 naming Central's http 8084) and slr.ws, because the APK is repacked with OPENRUNE_ENDPOINT=http://10.0.2.2:8080 (tracks/client/repack.sh, patch_server.py pads the URL to the original's length) and embedded Central serves one jav_config template, the desktops' (127.0.0.1 hosts). Embedded Central already serves /jav_config.ws and the world list (OpenRune-Central-Server centralHttpRoutes(worldListCache, javConfigCache)). Needed: the APK and the desktops read the same Central jav_config.ws and slr.ws, one sign-in path (e.g. adb reverse of the game, Central http and https ports so the emulator's 127.0.0.1 is the host's, the repack endpoint naming Central's http port; or another way that keeps one template), the http service, SIDECAR_DATA and the APK template leave compose and track.sh deploy, tracks/client/track.md's allowed sockets and its javcheck line follow. Privacy unchanged: javcheck.py passes on Central's /jav_config.ws with the APK's host, the repack keeps OPENRUNE=1 LOCAL_AUTH=1. Done when a deploy runs no osrs-openrune-http container and tracks/client/track.sh up <slug> reaches LOGGED_IN on it, and fork up's APK path likewise. Upstream blob shas: evidence/h-reference-deployment/upstream-shas.md (re-check before acting). Part of h-reference-deployment (PRD H8); found by run 316.
