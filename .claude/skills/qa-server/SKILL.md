---
name: qa-server
description: "The server reviewer's aggregate: how to judge every criterion of a server change once, from the change's own build, and the rows no other skill owns (no-raw-data, playable, style). Use as qa on a judge brief."
---
# QA, server (judgment; bring-up, build and gate are scripts)

Order of a judge run: `hd show <slug>` (the criteria, every prior verdict, the gate and build detail) →
`tracks/fork/track.sh up <slug> 2` (the same build the gate passed; two logged-in clients for social features) → every
row, in the order of the criteria → `hd verdict <slug> <head> rows.json` with every criterion `pass` or `fail: <note>`.

## Rows this skill judges
- **no-raw-data**: no game data or raw ids in Kotlin (lists, tables, timings belong in the cache or config); gameval
  symbols; state in varbits and varps. Fixed as a rule across the whole diff, not where one instance was named.
- **playable**: every flow playable without a cheat on the test server; evidence (dumps, container history, chat
  history) in the evidence dir; a blocker's repro passes.
- **style**: no added comments or KDoc, no unjustified test, nothing public for a test, no quirk entries, toggles in
  the config with a default, no deviation recorded instead of fixed.
  A test is justified only as one of: the dupe test of an item-moving flow (`dupes`); a test of one rule with several
  input cases, each case asserted; a test a reviewer asked for on the PR.
  A test of an interaction, a dialogue, a quest's stages or a script's flow is none of these, whatever the PR text
  says: `fail: <test file>: not a dupe test, a multi-case rule or a reviewer's request` so the dev removes it.

## Rows other skills judge
accuracy, rsprox, unsourced → `accuracy`; claims, no-deferral, net-change, one-change → `pr-text`; dupes → `dupes`.

## Verdict rules
- Every row judged, once; a row found failing later is a missed criterion: add the row before the next judge run.
- Text-only failures: fix the text, mark pass. Code failures: `fail: <what, where, the rule>` so the dev fixes the rule.
- Never write the code; never a caveat for a divergence; a disclosed gap is a FAIL.
- Read-heavy lookups (recordings, decompiled code, CI logs) go to a read-only subagent returning the conclusion.
