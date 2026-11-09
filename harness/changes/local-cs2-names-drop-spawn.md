---
slug: local-cs2-names-drop-spawn
track: fork
priority: P1
deps:
- h-pin-skip-cs2-spawn
- h-ref-pins-audit
---
# local: NameCs2Groups removes the spawn menu's clientscripts from the cache

Staging's NameCs2Groups (local-cs2-group-names, or-cache/src/main/kotlin/dev/openrune/pack/NameCs2Groups.kt, run after PackCs2 in PluginPacks.kt) removes every archive 12 group above the highest id in cs2Overrides.symbols["clientscript"]. That list holds only the quest pack's symbols (10197, 10198), not the spawn pack's (content/other/spawn/pack/.../symbols/clientscript.sym, 10199..10209), so the 11 spawn menu scripts are packed and then deleted. Seen on a server built from the fork's staging (tree 3b74775d8) with FileStore 45516d0: archive 12 of /app/.data/cache/SERVER and LIVE has 10189 groups, max id 10198, no group with the hash of any [clientscript,spawn_menu_*]; ::spawn opens interface 1099 with none of its scripts. The same FileStore head on tree 1cba46d39 (before NameCs2Groups) gave 10200 groups (evidence/filestore-cs2-group-name-hash/reftable.txt). The live server built from staging has the same loss. Root cause: the symbols merge or the removal range; the removal of groups above the custom range must count every pack's symbols (or go). Done when: a cache built from staging has groups 10197..10209 named with their symbol hashes, no hash-0 group in archives 6, 8, 10, 12, 13, and ::spawn on a desktop runs spawn_menu_init (10199). Unblocks filestore-cs2-group-name-hash's client proof (::spawn opening the item spawner).
