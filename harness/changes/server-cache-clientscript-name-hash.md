---
slug: server-cache-clientscript-name-hash
track: server
title: The served cache gives two clientscript groups an empty name hash; the mobile
  app dies on it
kind: change
priority: P2
deps: [harness-build-gate-keyed-process, harness-github-reads-budget, harness-carry-gh-pr-edit-classic-projects]
created: '2026-11-01T20:44:26Z'
---
The test server's cache (container osrs-openrune, image built 2026-11-01T19:21Z, /app/.data/cache/LIVE) has archive 12 (clientscripts) groups 10197 [clientscript,quest_available_set] and 10198 [clientscript,quest_policy_complete_set] with name hash 0 (the hash of the empty name). In the cache of image-ce529de (openrune-work, 2026-10-31 14:22) the same groups carry the hashes of their names (-265444471 and 460187852, Java String.hashCode of '[clientscript,<name>]'), as every other group does. Effect: the official Android app's loader reads file 'version.dat' from archive 12 (group 0); its by-name read first asks for a group named '' and, when one exists, looks 'version.dat' up as a file of that group, finds nothing and reads a u16 from a null buffer: SIGSEGV SEGV_MAPERR at osclient.so 0x4160ec (ldrh w20,[x10,x9]) while still at GameState UNKNOWN, right after the configs load. Proven in stock game code: with setprop debug.osrsrl.off 1 (no hooks, no host) it dies at the same pc (evidence/client-login-segv-osclient/logcat-stock-off.txt). Desktop Java clients do not read version.dat and are unaffected. Find the packing step that drops the two names (they are recent content/quest/pack scripts; the incremental_live cache files date 19:02) and keep every group's name hash, as in the official cache. Acceptance: no group of archive 12 in the served cache has name hash 0 (and the set of name hashes is distinct); a real client 'track.sh up' of the live build reaches LOGGED_IN.

Orchestrator (2026-11-01 23:05Z): its gate failed on CI for an external reason (GitHub quota 403 / openrs2 cache fetch), not its code; held until those fixes land so no dev run is spent on it.
