---
name: reverse
description: "Reverse-engineer the official OSRS Android client (liblibs.hal.system.osclient.so) with headless Ghidra, jadx or the in-app agent. Use to find or check offsets, struct layouts, xrefs, decompiled functions, patched bytes, or the client's side of the game protocol."
context: fork
---
# Reverse the Android client

Addresses: docs/offsets.md uses ELF addresses; Ghidra is ELF + 0x100000. Protocol notes: docs/android-protocol.md.

## Ghidra (headless, project `re/ghidra`, program `osclient`)
Use `-readOnly` unless the task is to update the project; only one writer at a time.
```
~/tools/ghidra_12.1.4_PUBLIC/support/analyzeHeadless re/ghidra osclient -process osclient.so -noanalysis -readOnly \
  -scriptPath tools/ghidra_scripts -postScript <Script>.java <args>
```
| Script | Args | Output |
|---|---|---|
| `Decompile.java` | Ghidra addresses (`0x76100c ...`) | `re/decomp/<entry>.c` per containing function |
| `Callers.java` | Ghidra addresses | per target: callers count, then one line per calling function with its call sites (`<no function>` = a site outside any function) and a count of non-call refs |
| `Xrefs.java` | Ghidra addresses | functions referencing each (every reference type) |
| `StringXrefs.java` | strings (`"Walk here"`) | functions referencing literals containing them |
| `FindScalar.java` | scalars (`0x89494`) | functions with an instruction using that operand (struct fields) |
| `FixSwitches.java` | none (`dry` to only report) | **writer**: completes switch tables auto-analysis missed; for re-building the project only |

### Cross-check caller claims against the whole binary
Ghidra only sees code it has disassembled. The first project missed switch arms whose jump tables auto-analysis
left unresolved or partial, so `Xrefs.java` found 1 of the 3 callers of the slr.ws parser ELF 0x4320dc without
any error. `re/ghidra` was rebuilt on 2026-10-18 (auto-analysis, `FixSwitches.java`, auto-analysis again):
instructions outside any function went from 8944 to 36 and `Callers.java 0x5320dc` now lists all 3 callers and
5 sites. A "who calls X" or "X is only reached from Y" claim still needs the whole-binary check:
```
aarch64-linux-gnu-objdump -d --no-show-raw-insn re/osclient.so | grep -E '\sbl?\s+4320dc\b'   # ELF addresses, ~2 s
```
Each hit is a call site; it must match `Callers.java` (ELF + 0x100000). A site Ghidra doesn't place in a
function is a gap in the project: map it with `Decompile.java` of the nearby function and say so. Indirect
calls (vtables, function pointers) don't show up either way; list them as not established, or find the table
with `FindScalar.java`.

Rebuilding the project (a new client build): import into a new dir, auto-analyse, `-postScript FixSwitches.java`
without `-readOnly`, auto-analyse again (`-process osclient.so` without `-noanalysis`), then swap dirs by
renaming while no Ghidra job runs (`GHIDRA_HEADLESS_MAXMEM=6G`; each pass ~4 min).

### Address conventions
ELF addresses in docs/offsets.md and in objdump; Ghidra = ELF + 0x100000. Passing an ELF address to a Ghidra
script doesn't fail: it is a valid address elsewhere in the program and returns nothing or the wrong function.
Always say which convention a number is in.

### Keep output small
Quote only the lines that support the claim (the call, the field offset); point to `re/decomp/*.c` for the rest.

## Other tools
- Java side of the APK: `~/tools/jadx/bin/jadx` (output under `re/`).
- Live memory: `tools/agent.py` (base, read, counters, findptr, watch) with `setprop debug.osrsrl.agent 1` and a
  restart; needs the device lock.

## Report
The addresses (say ELF or Ghidra), what each one is, and the evidence path (`re/decomp/*.c`, script output).
A claim you couldn't confirm is marked as a guess.
