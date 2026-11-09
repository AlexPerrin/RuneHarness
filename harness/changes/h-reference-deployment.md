---
slug: h-reference-deployment
track: harness
priority: P0
deps:
- h-dep-gate-failed-waits
- h-desktops-token-login
- h-ref-apk-jav-config-central
- h-ref-devtools-upstream
- h-ref-embedded-central
- h-ref-pins-audit
- h-ref-rsprox-targets
- h-ref-server-bundle
---
# The local stack is a reference OpenRune deployment (PRD H8)

The user's word: "Our local environment should be a reference OpenRune deployment, properly use these tools and how they are meant to integrate." Read the live upstream sources first and record their blob shas: OpenRune-Server .github/workflows/release-server.yml and update-test-server.yml, docs/RELEASE_CI.md, game.example.yml, README Client Setup; OpenRune-Central-Server README and central-config.example.yaml; OpenRune-Developer-Tools README.

Upstream's shape as read 2026-11-07: the server is built by `:or-cache:freshCache :or-cache:mergePluginGamevals :server:app:shadowJar` from game.example.yml, bundled as server.jar, game.yml and .data/ (no raw-cache), run by `java -jar server.jar` in that directory. game.example.yml defaults to central.same-instance: true on link port 9091; the test-server workflow names ports 43594 (game), 9091 (central), 9090 (http). The client connects through RSProx with a proxy-targets entry (jav_config_url, revision, modulus from .data/client.key). OpenRune-Developer-Tools is the sideloaded MCP plugin.

Needed: tracks/fork/build and the deploy build and run that bundle on staging's tree (a container may wrap it; the steps inside are upstream's, not `install`'s server/bin/app). `up`, live-desktop and the deploy all use embedded Central on upstream's ports for jav_config and sign-in, with no issuer, http or http-desktop container. Desktops connect through RSProx's proxy-targets as the README says. Audit every hd.yaml pin: one a reference deployment makes unneeded goes (local/local-auth is the first to check), each kept one gets its reason. Compare our devtools plugin with OpenRune-Developer-Tools and adopt upstream's where it does the job, or name why not.

Deviations to keep, each named in docs/ARCHITECTURE.md with its reason: the local jav_config instead of client.blurite.io (Privacy: no client contacts Jagex, and that config names Jagex hosts); Central's sign-in and token login, ours until the Central upstream hold lifts; the patched APK. No Privacy rule weakens for the reference.

FileStore and Developer-Tools are part of the reference (the user's word): the cache is built by OpenRune-FileStore as upstream's `or-cache` does (the published `dev.or2:filestore`, our staged FileStore head where a filestore change is on staging), with no harness cache step beside it; the desktops' devtools are OpenRune-Developer-Tools where it does the job (h-ref-devtools-upstream), each kept tool of ours named with its reason.

Done when, from a clean state, the staging deploy and `up` on a fresh C:\osrs-test home reach LOGGED_IN on the desktop and the APK with those containers gone, javcheck.py passing on Central's own /jav_config.ws, and ACCEPTANCE H8 replaced by the observed fact. If it is too large for one run, file its parts as changes, each with its deps, and hand back.
