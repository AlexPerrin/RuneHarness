---
name: qa-server
description: "The server reviewer's aggregate: how to judge every contract row of a server change once, from the change's own build, and the rows no other skill owns (no-raw-data, playable, style). Use as qa on a judge brief."
---
# QA, server (judgment; bring-up, build and gate are scripts)

Order of a judge run: `hd show <slug>` (the contract, every prior verdict, the gate and build detail) →
`tracks/server.sh up <slug> 2` (the same build the gate passed; two logged-in clients for social features) → every
row, in the order of the contract → `hd verdict <slug> <head> rows.json` with every row `pass` or `fail: <note>`.

## Rows this skill judges
- **no-raw-data**: no game data or raw ids in Kotlin (lists, tables, timings belong in the cache or config); gameval
  symbols; state in varbits and varps. Fixed as a rule across the whole diff, not where one instance was named
  (v7 cause: `MailDye` fixed, `ARMOURS` next round).
- **playable**: every flow playable without a cheat on the test server; evidence (dumps, container history, chat
  history) in the evidence dir; a blocker's repro passes.
- **style**: no added comments or KDoc, no unjustified test, nothing public for a test, no quirk entries, toggles in
  the config with a default, no deviation recorded instead of fixed.

## Rows other skills judge
accuracy, rsprox, unsourced → `accuracy`; claims, no-deferral, net-change, one-change → `pr-text`; dupes → `dupes`.

## Verdict rules
- Every row judged, once; a row found failing later is a contract miss: add the row before the next judge run.
- Text-only failures: fix the text, mark pass. Code failures: `fail: <what, where, the rule>` so the dev fixes the rule.
- Never write the code; never a caveat for a divergence; a disclosed gap is a FAIL.
- Read-heavy lookups (recordings, decompiled code, CI logs) go to a read-only subagent returning the conclusion.
