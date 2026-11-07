---
slug: central-embedded-jav-config
track: central
priority: P1
deps:
- central-rights-test-mod
- h-central-up-desktop-jav
---
# embedded Central serves a local jav_config of its own, set from the server's environment

Embedded Central (central.same-instance) builds its config in centralRuntimeConfigFromJdbc (central-app/src/main/kotlin/dev/or2/central/util/config/CentralRuntimeConfig.kt), whose javConfig is fixed: it fetches https://client.blurite.io/jav_local_238.ws (revision 238; codebase http://127.0.0.1/, param 17 https://client.blurite.io/world_list.ws, params 2, 11, 13, 19, 20 and terms/privacy/advert URLs naming jagex.com, runescape.com and googleusercontent.com) and the fork passes no override (api/net/.../central/embed/CentralEmbeddedLifecycle.kt). So /jav_config.ws of the game's own Central can serve no client of the test server: wrong revision, foreign world list, Jagex hosts (tracks/fork/server/javcheck.py fails it), and tracks/central/track.sh up token (h-central-up-sign-in) cannot drop the http-<slug> sidecar nor point the desktop's OPENRUNE_ENDPOINT at Central as central-game-session's G8/G9 require. Needed: embedded Central's /jav_config.ws a local jav_config with no remote fetch (e.g. a template file, as tracks/fork/server/jav_config.ws.template the http sidecar serves: revision 241, codebase and param 17 naming the game's host and Central's worldslist.ws, no foreign host), its source set from the server's environment as signIn and http.tls already are (CentralConfig.fromEnvironment), so the harness sets it per up and the deploy without a sidecar. Judge: javcheck.py passes on http://127.0.0.1:<central http>/jav_config.ws of an up built with the head, and a desktop pointed at it reaches the game.
