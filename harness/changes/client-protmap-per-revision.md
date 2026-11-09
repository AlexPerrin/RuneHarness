---
slug: client-protmap-per-revision
track: client
priority: P2
---
# Android protocol mapping per revision: scripted extract, match, generate and validate (tools/protmap)

The user (2026-11-09): osrs-plugins-reverse maintains the Android game-protocol mapping. Every revision is mapped as it ships, each revision's mapping is kept, and the process improves over time. 241 is mapped by hand (docs/android-protocol.md, the osrs-241-android module in server/rsprot.patch); 242 (fork-android-rsprot-242) is the first revision through this tooling.

## Findings (rsprot desktop 221-242, Android 241; driver analysis 2026-11-09)
- Opcodes are re-randomised every revision: desktop keeps 0-9 of ~150 server->client and 0-7 of ~100 client->server from one revision to the next. Android is its own permutation (7 of 147 S->C and 2 of 78 C->S equal desktop 241; no offset or XOR relation). No rotation pattern predicts them.
- Layouts change too: desktop 241->242 changed the field order or byte transforms (Alt1/2/3) of 75 of 139 S->C and 47 of 84 C->S packets with fields.
- Invariants: each packet's size and its multiset of field widths (0 of those changed 241->242). Android's size tables are permutations of desktop's (docs/android-protocol.md).
- Identification power on 242: size alone 8 of 152 S->C and 5 of 109 C->S; size + field widths at least 73 of 152 and 32 of 109 (lower bounds, rough parser). The rest (e.g. 11 empty S->C packets, 13 size-3 OPNPC/OPLOC/OPOBJ C->S ops) need the previous revision's map carried over by code similarity (callees, string xrefs, constants, the menu op a sender passes).

## The change
tools/protmap/ in osrs-plugins-reverse:
1. extract (headless Ghidra over a revision's liblibs.hal.system.osclient.so, built on tools/ghidra_scripts FixSwitches/Xrefs/FindScalar): both size tables; per S->C opcode its dispatcher case's read sequence (width + transform, by the docs/android-protocol.md byte-transform table); per C->S opcode its packet-constructor call site and write sequence; per handler/sender the callees, strings and constants for carry-over.
2. match: each opcode to an rsprot desktop prot of the same revision by size + field widths, then the previous revision's Android map by code similarity; what stays ambiguous is listed for a person, with its candidates.
3. generate: the osrs-<rev>-android module (prot enums, codecs: the layout is the client's own read/write sequence) and the docs tables.

Per-revision record: protmap/<rev>/ keeps that revision's extracted tables, the final mapping (opcode -> prot, size, layout, how it was identified: size / widths / carry-over / by hand / dead), and a diff against the previous revision. A process log per revision (protmap/PROCESS.md, one row per revision) records the counts: identified automatically by each method, by hand, dead, open, validation failures found, and what changed in the tooling for the next revision. The aim is fewer by-hand rows each revision.

## Validation (cheapest first)
1. static, on every generation: each size-table entry equals rsprot's size for the prot it is mapped to; the client's field widths equal rsprot's; every opcode named or dead; progress.py counts against the previous revision.
2. generated round-trip test per packet: encode with the Android codec, decode with a reader generated from the client's read sequence, values equal.
3. one live run on the emulator: a scripted play sequence (login, walk, chat, interfaces, bank, npc/loc/obj ops) with the server's IncomingPacketTrace/OutgoingPacketTrace on: zero decode failures, no disconnect; for the packets it triggers, the devtools MCP checks the effect (varp, widget text, inventory).

Done when: tools/protmap regenerates 241 from the 241 .so to the same mapping as the hand-made one (the bench: every difference explained), protmap/241/ and protmap/PROCESS.md exist, and the 242 mapping is produced through it with static and round-trip checks green, handed to fork-android-rsprot-242.

## retry after run 418
The user (2026-11-09): retry. Run 418 handed back 'ask' with no question recorded, after a safety classifier stopped its response twice while it read rsprot's byte-transform helpers (JagexByteBufExtensions.kt); its withheld output and tool calls never ran. Start from the brief's findings; ask with hd ask (a recorded question) if a decision is needed.
