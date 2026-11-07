---
slug: filestore-cs2-group-name-hash
track: filestore
priority: P2
deps:
- h-filestore-build
- h-filestore-up-login
---
# FileStore: name each packed clientscript group in the cache reference table (moved from OpenRune-Server #448)

OpenRune/OpenRune-Server#448 (closed) fixed this in the server's cache tools; the maintainer, Mark7625, asked: 'could you please pr this to https://github.com/OpenRune/OpenRune-FileStore instead please so its built into current cs2 system'. The defect: every clientscript a plugin pack adds (archive 12 groups 45500..45530 of the spawn menu, 45550 and 45553 of the quest pack) is packed with name hash 0. A client that reads an archive file by name trips on it: the official Android client reads version.dat (group 0) by name, and its lookup of the empty name finds a group with hash 0 first. Make FileStore's cs2 packing write each packed script's group name hash (the hash of its script name) into the reference table, so no group of archives 6, 8, 10, 12 or 13 carries hash 0 and no two share a hash. The server-side version is on the fork as dev/server-cache-clientscript-name-hash (c383a5111, NameCs2Groups.kt, run after PackCs2): take its logic, not its place. Then a server change bumps the FileStore version (ARCHITECTURE §11). Proof as on #448: the built cache's reference table, and a desktop login with the pack scripts running (45550 and 45553 at login, ::spawn opening the item spawner).
