---
slug: local-cs2-group-names
track: fork
priority: P0
---
# local: name the cache's clientscript groups so the Android app starts on the live server

The live cache (osrs-openrune /app/.data/cache/LIVE, deployed at the cutover, 02888f562a74) has 15 groups of archive 12 with name hash 0: 10197, 10198, 45500..45530 (every third), 45550, 45553. The official Android app reads version.dat of archive 12 by name; its lookup trips on the hash-0 groups, gets no buffer and reads a u16 from null, at ELF 0x4160ec in liblibs.hal.system.osclient.so (Client+0x23a8 is archive 12; called from 0x412e78 in doCycle). The app dies 16s after start on every start: SIGSEGV, fault addr 0, backtrace and hash listing in evidence/local-cs2-group-names/. tracks/client/mobile_login.py reports it as FAILED: the app died, and track.sh up and measure never log a mobile in. RuneLite desktops are not affected.

The fix exists: c383a5111 (fork dev/server-cache-clientscript-name-hash, NameCs2Groups in or-cache), which merges cleanly on staging fd6c1dd4c. The upstream-shaped fix is filestore-cs2-group-name-hash, which cannot land soon: it waits on h-filestore-up-login, then on token login. Carry c383a5111 on staging until then; drop it when the FileStore change lands. It stays local, upstream asked for the fix in FileStore.

Done when: a cache built from the tree has no group with hash 0 and no duplicate hash in archive 12, all 15 groups included (reftable.py in evidence/filestore-cs2-group-name-hash; if 10197, 10198 or 45500..45530 are not named by NameCs2Groups, fix that), and tracks/client/track.sh up against that server prints LOGGED_IN or a login result past the crash.
