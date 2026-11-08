---
slug: h-ref-server-bundle
track: harness
priority: P0
---
# tracks/fork build and the deploy build and run upstream's release bundle

tracks/fork/track.sh build and the staging deploy build staging's tree the way upstream's release-server.yml does: ./gradlew :or-cache:freshCache :or-cache:mergePluginGamevals :server:app:shadowJar from game.example.yml, bundled as server.jar, game.yml and .data/ (no raw-cache), and run it by java -jar server.jar in that directory (a container may wrap it; the steps inside are upstream's, never install's server/bin/app). Ports as update-test-server.yml: 43594 game, 9091 central link, 9090 http. Each harness setting the bundle needs beyond game.example.yml is named with its reason. Done when up and the deploy run the bundle and a desktop reaches LOGGED_IN on it. Upstream blob shas: evidence/h-reference-deployment/upstream-shas.md (re-check before acting). Part of h-reference-deployment (PRD H8).
