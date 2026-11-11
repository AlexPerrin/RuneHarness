---
slug: client-api-probe-242
track: client
priority: P2
deps:
- fork-staging-merges-main-242
---
# The api-probe and client-state.md re-run on the 242.3 client against the deployed 242 server

client-android-242 (branch client/client-android-242, 43284c3) ports the native hooks and the repack to the official Android 242.3 APK. On the live revision-241 stack its build boots, the build is recognised, every hook installs, check-blocked passes and 4 plugins start (evidence/client-android-242/boot-242-logcat.txt), but login stops at game state 2 (js5) because a 242 client cannot load from a 241 server. Its api-probe and docs/client-state.md therefore wait for the 242 server live (fork-staging-merges-main-242 deployed). Done when tools/api-probe.sh on that build's mobile logged in to the 242 live stack passes at least the 241.4 result (94.1%, 1178/1252), every failing row is explained or fixed, and docs/client-state.md carries the new result.
