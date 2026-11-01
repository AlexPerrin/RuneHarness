#!/usr/bin/env python3
"""Regenerates server-content.json: one row per content unit, read from the files osrs-mcp serves (the decoded LIVE
cache and gamevals.dat under $SERVER_TOOLS/src/.data). The unit kinds are the dbtables in KINDS, defined in
server-content.md. Rows already in the inventory keep their `passes`; a new row starts false.
usage: harness/goals/server-content.py [out.json]"""
import bz2, json, os, struct, sys, zlib
from pathlib import Path

KINDS = {"quest": ("quest", "quest_"), "skill": ("hiscores_skill_info", "hiscores_skill_"), "minigame": ("minigame_teleport", "minigame_"),
         "boss": ("hiscores_bosses_info", "hiscores_bosses_")}   # kind: (dbtable, row-name prefix dropped from the unit)
DATA = Path(os.environ.get("SERVER_TOOLS", Path.home() / "src/openrune-work/server-tools")) / "src" / ".data"


class Buf:
    def __init__(s, b): s.b, s.o = b, 0
    def u8(s): s.o += 1; return s.b[s.o - 1]
    def u16(s): s.o += 2; return struct.unpack_from(">H", s.b, s.o - 2)[0]
    def i32(s): s.o += 4; return struct.unpack_from(">i", s.b, s.o - 4)[0]
    def smart(s): return s.u8() if s.b[s.o] < 128 else s.u16() - 32768
    def big_smart(s): return s.i32() & 0x7fffffff if s.b[s.o] >= 128 else s.u16()
    def string(s): e = s.b.index(0, s.o); v = s.b[s.o:e].decode("cp1252"); s.o = e + 1; return v
    def var_int(s):  # readVarInt2: 7 bits per byte, low first
        v = sh = 0
        while True:
            x = s.u8(); v |= (x & 127) << sh; sh += 7
            if x < 128: return v


def gamevals(table):
    """{id: name} of one gamevals.dat table: int tables; per table utf name, int count, utf "name=id" entries."""
    b = Buf((DATA / "gamevals-binary" / "gamevals.dat").read_bytes()); out = {}
    for _ in range(b.i32()):
        name = b.u16(); name = b.b[b.o:b.o + name].decode(); b.o += len(name.encode())
        for _ in range(b.i32()):
            n = b.u16(); k, _, v = b.b[b.o:b.o + n].decode().rpartition("="); b.o += n
            if name == table: out[int(v)] = k
    return out


class Cache:
    def __init__(s, d): s.d = d; s.dat = (d / "main_file_cache.dat2").read_bytes()

    def raw(s, index, group):
        idx = (s.d / f"main_file_cache.idx{index}").read_bytes()[group * 6:group * 6 + 6]
        size, sector = int.from_bytes(idx[:3], "big"), int.from_bytes(idx[3:], "big")
        out, big = bytearray(), group > 0xffff
        while len(out) < size:
            p = sector * 520 + (10 if big else 8)
            n = min(size - len(out), 510 if big else 512)
            out += s.dat[p:p + n]; sector = int.from_bytes(s.dat[p - 4:p - 1], "big")
        return bytes(out)

    def container(s, index, group):
        b = s.raw(index, group); comp, n = b[0], struct.unpack_from(">i", b, 1)[0]
        if comp == 0: return b[5:5 + n]
        data = b[9:9 + n]
        return bz2.decompress(b"BZh1" + data) if comp == 1 else zlib.decompress(data, 31)

    def files(s, index, group):
        """{file id: bytes} of one group, from the index's reference table."""
        r = Buf(s.container(255, index)); proto = r.u8()
        if proto >= 6: r.i32()
        flags = r.u8(); count = r.big_smart() if proto >= 7 else r.u16()
        ids, last = [], 0
        for _ in range(count): last += r.big_smart() if proto >= 7 else r.u16(); ids.append(last)
        if flags & 1: r.o += 4 * count
        r.o += 4 * count                                          # crcs
        if flags & 4: r.o += 8 * count                            # sizes
        if flags & 2: r.o += 64 * count                           # whirlpool
        r.o += 4 * count                                          # versions
        fcounts = [r.big_smart() if proto >= 7 else r.u16() for _ in ids]
        fids = {}
        for g, c in zip(ids, fcounts):
            last, fids[g] = 0, []
            for _ in range(c): last += r.big_smart() if proto >= 7 else r.u16(); fids[g].append(last)
        names = fids[group]; data = s.container(index, group)
        if len(names) == 1: return {names[0]: data}
        chunks = data[-1]; t = Buf(data); t.o = len(data) - 1 - chunks * len(names) * 4
        sizes = [[0] * len(names) for _ in range(chunks)]
        for c in range(chunks):
            n = 0
            for f in range(len(names)): n += t.i32(); sizes[c][f] = n
        out, o = {f: b"" for f in names}, 0
        for c in range(chunks):
            for f, fid in enumerate(names): out[fid] += data[o:o + sizes[c][f]]; o += sizes[c][f]
        return out


def dbrow_table(b):
    """The dbtable id of one dbrow definition (config group 38): opcode 3 columns, 4 table id, 0 end."""
    r, table = Buf(b), None
    while (op := r.u8()) != 0:
        if op == 3:
            r.u8()
            while (col := r.u8()) != 255:
                types = [r.smart() for _ in range(r.u8())]
                for _ in range(r.smart()):
                    for t in types: r.string() if t == 36 else r.i32()
        elif op == 4: table = r.var_int()
        else: raise ValueError(f"dbrow opcode {op}")
    assert r.o == len(b), "dbrow not fully read"
    return table


def inventory(old):
    tables = {v: k for k, v in gamevals("dbtable").items()}
    names, passes = gamevals("dbrow"), {r["unit"]: r["passes"] for r in old}
    kind = {tables[t]: k for k, (t, _) in KINDS.items()}
    rows = []
    for rid, b in sorted(Cache(DATA / "cache" / "LIVE").files(2, 38).items()):
        t = dbrow_table(b)
        if t in kind:
            name = names.get(rid, str(rid))
            table, prefix = KINDS[kind[t]]
            unit = f"{kind[t]}:{name.removeprefix(prefix)}"
            rows.append({"unit": unit, "source": f"dbrow.{name}={rid} dbtable.{table}={t}", "passes": passes.get(unit, False)})
    assert rows and len({r["unit"] for r in rows}) == len(rows), "empty inventory or duplicate units"
    return rows


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).with_suffix(".json"))
    rows = inventory(json.loads(out.read_text()) if out.exists() else [])
    out.write_text(json.dumps(rows, indent=1) + "\n")
    print(f"{out}: {len(rows)} rows, " + ", ".join(f"{k} {sum(r['unit'].startswith(k + ':') for r in rows)}" for k in KINDS))
