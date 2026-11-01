---
slug: harness-central-include-app
track: harness
title: A server build with CENTRAL substitutes Central's app module too
kind: change
priority: P0
deps: []
created: '2026-11-01T04:29:59Z'
---
The server track's build (tools/track.sh build, local/harness of OpenRune-Server) includes a change's Central tree with -Popenrune.central.includeBuild=<dir>. Gradle substitutes only modules named like the included projects (dev.or2:central-common, dev.or2:central-worldlink); the server's embedded Central is dev.or2:openrune-central (Central project :central-app, artifactId openrune-central), which stays the published jar. Observed in server-token-auth-4: with openruneCentral bumped to 2.0.3 (the version that will carry central-token-login-op), the build fails 'Could not find dev.or2:openrune-central:2.0.3' (state/server-token-auth/build-01982cbc0c509787d0bb01db14cd89d68bd3c625-c0485930ffdf3.log); at 2.0.2 it would mix the new worldlink (PROTOCOL_VERSION 9) with the old embedded app that has no token LOGIN handler. Fix: the build includes the Central tree with a dependency substitution of dev.or2:openrune-central to project :central-app (e.g. a Gradle init script with settingsEvaluated { includeBuild(dir) { dependencySubstitution { substitute(module("dev.or2:openrune-central")).using(project(":central-app")) } } } in place of the -P property), so every Central module of a server build with CENTRAL is the Central tree's, whatever version libs.versions.toml names. Check: a server build of server-token-auth (fork dev/server-token-auth 76413e15e, deps central-token-login-op) succeeds and its image's lib holds the central-app built from the Central tree.
