---
slug: h-client-build-debuggable
track: harness
priority: P1
---
# the client track's build repacks with DEBUGGABLE=1

client-local-auth-debuggable (run 340) adds DEBUGGABLE=1 to tools/repack.sh (android:debuggable on <application>, a 'patched ... debuggable' repack line) as its own switch; tools/release-dev.sh unsets it and refuses a debuggable APK (tools/not-debuggable.sh). The user's word (2026-11-09): the agents' build sets it, the release never. Needed: tracks/client/build/build.sh build passes DEBUGGABLE=1 on its repack line beside MODULUS SERVER OPENRUNE LOCAL_AUTH (no other change; the cache stays keyed by T: a tree whose repack.sh has the switch is built debuggable). Done when: the build of client-local-auth-debuggable's tree logs 'patched ... debuggable' and its APK fails tools/not-debuggable.sh, with no env var set by the caller.
