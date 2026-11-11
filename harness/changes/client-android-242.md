---
slug: client-android-242
track: client
priority: P2
deps:
- fork-staging-merges-main-242
---
# The client ships the official Android 242 APK, its native hooks ported to the 242 .so

Run 423 (fork-android-rsprot-242): RSProt 1.0.0-ALPHA-20261106.100 with the osrs-242-android module rebuilt from 242-derived tables is published to ~/src/OpenRune-Server/.m2-rsprot (patch evidence/fork-android-rsprot-242/rsprot.patch; tables c2s-242-layouts.txt, s2c-242-layouts-*.txt, ext-zone-242.txt there). Its done condition, the official Android 242 client logging in and playing on a server built from dev/fork-staging-merges-main-242, needs a 242 client build, which the client track cannot make: tracks/client/build/build.sh links the repo-root base.apk/split_config.arm64_v8a.apk (241.4), and the native hooks are 241 .so offsets (native/src/game.cpp, script_hooks.cpp, draw_hide.cpp, npc_probe.cpp, friends_probe.cpp, host AndroidClient.java, tools/agent.py). The 242 pair is ~/osrs-plugins-reverse/242/ (base.apk sha256 c0b6e906...376e, split_config.arm64_v8a.apk c970da69...abcc8); the 242 .so, its Ghidra project and decompiles are under ~/osrs-plugins-reverse/re/242/ with the 242 packet addresses in evidence/fork-android-rsprot-242/handoff.md. Done when an OPENRUNE=1 LOCAL_AUTH=1 build from the 242 APKs boots, passes check-blocked, and its plugins load on the 242 client; the RSProt change's live test (login and play against a 242 server) then runs on it.
