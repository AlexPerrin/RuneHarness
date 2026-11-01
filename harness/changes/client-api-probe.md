---
slug: client-api-probe
track: client
kind: change
title: 'tools/api-probe.sh: runtime probe of every net.runelite.api interface method
  in the Android app, percentage and per-method report'
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T13:57:43Z'
goal: client-api
---
## Change
The goal's measure command `tools/api-probe.sh` (harness/goals/client-api.md) does not exist in the client repo, so
client-api cannot be measured (orchestrator run client-api-1, base 6b2003e). The only number today is the static one,
`tools/progress.py --dry-run`: "RuneLite API implemented 661/866 76.3%" over 14 host-backed interfaces (Client
222/325, NPC 47/79, Player 51/80, Scene 14/36, Widget 152/160, WorldView 23/27, Tile 13/17, NPCComposition 24/26,
ItemComposition 42/43). It counts declarations, not working calls, and covers 14 of the 103 interfaces in
re/runelite/runelite-api-1.13.1.jar, which declare 1286 abstract methods (Client 318, widgets.Widget 160, Actor 63,
ItemComposition 36, Model 35, MenuEntry 31, Scene 28, WorldView 27, Projectile 26, hooks.Callbacks 26, ...).

Build the probe:
- A probe plugin jar for the Android plugin host that, logged in on the test server, reaches a live instance of each
  interface (Client, local Player, an NPC, WorldView, Scene, Tile, TileObject, TileItem, a Widget, ItemContainer,
  compositions, Menu/MenuEntry, MessageNode, Projectile, Model, ...), calls every abstract method of every
  net.runelite.api interface by reflection with safe arguments, and classifies each: pass (value of the declared
  type, no exception), throw (exception class and message), inert (resolves to a generated *Stub/*Bag or Inert
  path), unreached (no live instance; says which), and for setters and methods mapped to native hooks a round trip
  or observed effect (set then get, or the client state the hook changes) as the evidence.
- `tools/api-probe.sh [out-dir]` (default ~/osrs-harness/evidence/client-api/) on the caller's own BlueStacks instance
  (`ANDROID_SERIAL`): pushes the jar, runs the probe, pulls the report, prints one line with the percentage
  (pass / denominator), and writes the per-method report (interface, method signature, result, evidence) to the out
  dir. The denominator is every abstract method declared on a net.runelite.api interface in the shipped
  runelite-api jar; an interface the client is the caller of rather than the implementer (e.g. hooks.Callbacks) is
  excluded only by an explicit list in the report header with the reason. Unreached counts as not passing.
- Destructive or session-ending methods (logout, world hop, setGameState and the like) are called only where the probe
  can observe and undo the effect; otherwise they are listed as skipped with the reason and count as not passing.
- The probe removes its jar when done (by name, device-test step 6) and never touches the tester account's items or
  GE offer.

## Definition of done
- On a client build at the change's head, `tools/api-probe.sh` run twice on the dev's own emulator logged in
  on the test server prints the same percentage both times and writes a report with one row per denominator method
  (row count equals the printed denominator; the header lists the jar version, build sha and any excluded interface).
- Spot check in the hand-over: three pass rows, three throw or inert rows and one native-hook row, each matching what
  osrs-devtools shows for the same call or state.
- The device is restored (device-restore-check.sh check all OK) and the probe jar is gone from plugins/.
