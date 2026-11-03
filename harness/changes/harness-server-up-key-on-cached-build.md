---
slug: harness-server-up-key-on-cached-build
track: harness
title: server up has the change's RSA key when its image was cached
kind: change
priority: P1
deps: []
created: '2026-11-01T05:49:39Z'
---
tools/track.sh (server) copies game.key and client.key into state/<slug>/key only in build's uncached path (line 136). When or:<T> was built by another slug, build prints 'cached' and state/<slug>/key stays empty; up then bind-mounts the missing paths, docker creates them as root-owned directories, and the server exits at boot: GameServerLogbackCopy 'Source logback file logback.novice.xml not found' (ensureProperInstallation sees no game.key). Seen on quest-dorics at base T 9a551147e (built by harness-no-powershell). Fix: up (or the cached build path) provides a key pair when state/<slug>/key lacks one, e.g. generate it with openssl, and never lets docker create the mount sources; a test reproduces a cached build followed by up.
