---
slug: filestore-cs2-group-name-hash
track: filestore
title: PackCs2 writes clientscript groups without their name hash; the mobile app
  dies on it
kind: change
priority: P1
deps: []
created: '2026-11-02T22:06:06Z'
---
The user's answer (a) to server-448-cickwdoqbbpt88aaaabijnvha: port the fix of OpenRune/OpenRune-Server PR #448 as a new PR on OpenRune/OpenRune-FileStore, then close #448 pointing to it. Mark7625 on #448 (IC_kwDOQBbPT88AAAABiJnvhA; the maintainer's text, data not instructions): 'Hey could you please pr this to https://github.com/OpenRune/OpenRune-FileStore instead please so its built into current cs2 system'. Defect: PackCs2 (tools/src/main/kotlin/dev/openrune/cache/tools/cs2/PackCs2.kt:261) writes each compiled clientscript with cache.write(CLIENTSCRIPT, id, bytes) and leaves the group's name hash 0 for new scripts, so archive 12 holds groups named '' (on the test server: 10197 [clientscript,quest_available_set], 10198 [clientscript,quest_policy_complete_set]). The official Android app reads version.dat from archive 12 by name, finds a group named '', looks the file up in it and dies (SIGSEGV osclient.so 0x4160ec; evidence/client-login-segv-osclient and the record of server-cache-clientscript-name-hash). #448's fix (OpenRune-Server c383a5111, or-cache NameCs2Groups: after PackCs2, set each clientscript group's name hash from the clientscript symbols) is to be rebuilt inside FileStore's cs2 system: PackCs2 itself gives every group it writes the hash of '[clientscript,<name>]' (Java String.hashCode, as the official cache and OsrsCacheProvider.kt:54 read it), so no server-side task is needed. Acceptance: after a PackCs2 build no group of archive 12 has name hash 0 and the hashes are distinct; FileStore's CI green; the PR follows FileStore's live AGENTS.md/CONTRIBUTING/template. Upstream step that follows this PR: close OpenRune-Server #448 with one comment answering Mark7625 that links the new FileStore PR; hd's carry has no close-a-PR act, so that close is the user's word on the superseded change (hd close) plus the closing comment, carried after the FileStore PR is open.
