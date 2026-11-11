---
slug: fork-android-rsprot-242
track: fork
priority: P2
upstream: false
---
# local/android: the RSProt Android module's 242 tables, from the official Android 242 client

Run 414 (2026-11-09): staging's move to rev 242 (dev/fork-staging-merges-main-242 771fc8cd8, upstream main fccf79f82 merged onto staging, libs at rsprot 1.0.0-ALPHA-20261106.100 osrs-242-*) needs a 242 build of our RSProt Android module. The 241 patch (evidence/local-android-rsprot-token-gjstr/rsprot.patch) ported to upstream RSProt 00b2e758 (1.0.0-ALPHA-20261106, protocol/osrs-242) applies by 3-way: evidence/fork-staging-merges-main-242/rsprot-242-wip.patch. Its api, shared (MOBILE_TOKEN_AUTHENTICATION 7), protocol and desktop parts carry over as-is (UpdateStockMarketSlotV2Encoder's slot fix is upstream in 242, so ours is dropped). Its whole osrs-242-android module is still the 241 client's data and must not land: the 241 Android tables share 2 of 102 client opcodes with desktop, so they are per build and per revision.

Source: the official Android 242 APKs the user supplied, ~/osrs-plugins-reverse/242/base.apk (sha256 c0b6e906...376e) and split_config.arm64_v8a.apk (sha256 c970da69...abcc8): lib/arm64-v8a/liblibs.hal.system.osclient.so, 11196464 bytes. It needs a new Ghidra project (the reverse skill's rebuild steps; re/ghidra is 241's).

What is still to derive from the 242 .so (the reverse skill), each against docs/android-protocol.md's 241 entry:
1. Client->server size table: 241 had 102 int32 at .rodata 0x109538. In 242 the nearest match is at file offset 0x10b8dc with about 105-107 entries (multiset distance 5; evidence/fork-staging-merges-main-242/size-tables.txt, sizes.py). Confirm its length from the packet writer's bound.
2. Server->client size table: 241 had 151 int32 at 0x104c4c. In 242 it is at 0x1070bc with about 153 entries (distance 2). Confirm from the packet reader (241: 0x5da16c).
3. AndroidGameClientProt: all 102 opcodes and sizes, plus the client packets 242 added (upstream RSProt 242 now has OpLocTV1/OpLocTV2, OpLoc6V1/V2 and OpLocV2/V3 in osrs-242-model). Each from its sender as in 241 (packet constructor 241 0x79cc90).
4. AndroidGameServerProt: all 151 opcodes, plus the 242 additions, from the reader's dispatcher jump table (241: vaddr 0x1040f6).
5. The field byte orders (Alt1/2/3, order of fields) of every decoder in AndroidDecoders.kt and AndroidMoreDecoders.kt and every encoder in AndroidEncoders.kt, AndroidMoreEncoders.kt, AndroidZone.kt, AndroidLowResolutionChangeEncoder.kt, AndroidPlayerAppearanceEncoder.kt, AndroidPlayerHitsEncoders.kt, the two extended-info writers (NpcAvatarExtendedInfoAndroidWriter.kt, PlayerAvatarExtendedInfoAndroidWriter.kt: block flags and order) and unverified/*.
6. Compile against the 242 model: AndroidDecoders.kt:185-190 use OpLocT, which 242 split into OpLocTV1/OpLocTV2 (the 242 build stops there, evidence/fork-staging-merges-main-242/rsprot-publish.log).

Done when RSProt 1.0.0-ALPHA-20261106.100 (osrs-242-*, android included) is built from that patch with only 242-derived tables and published to ~/src/OpenRune-Server/.m2-rsprot, the patch kept as evidence/fork-android-rsprot-242/rsprot.patch, and the official Android 242 client (OPENRUNE=1 LOCAL_AUTH=1 build of the client track) logs in and plays on a server built from dev/fork-staging-merges-main-242. Then fork-staging-merges-main-242 builds and is submitted.
