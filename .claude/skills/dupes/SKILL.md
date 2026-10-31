---
name: dupes
description: "Prove no item-moving flow in a server change can duplicate or lose an item: the dev writes the dupe tests upstream's way, qa checks each flow's four paths in tests and in game. Judges the contract row dupes; the script row dupe-tests names the flows."
---
# Dupes (judgment; the flows come from the script)

Facts: `tracks/server/text.py dupes` lists every module whose main sources gain an item-moving call (`inv*` of
`api/invtx` and `ProtectedAccess`, `wornUnequip`, `objRepo.add/del`, shop ops) and fails one with no test source
added or changed. Upstream's rule: AGENTS.md "Unit tests" on upstream `main`, re-read live.

## The dev: one test class per flow, built like upstream's own (`FoundryRewardTransactionsTest.kt`, `BullBonesTest.kt`)
1. No space: full inventory, bank or slot mid-action → whole action rolls back.
2. Overflow: a stack at `Int.MAX_VALUE - n + 1` and at exactly `Int.MAX_VALUE - n` → all or nothing.
3. Repeats and races: the action twice in one tick; the source gone between check and take.
4. Accounting: every obj's total (inventory, worn, bank, ground) before and after differs by exactly the intent.
A path that cannot occur: one plain line in the PR notes. Test names say the behaviour. Nothing public for a test.

## qa: each flow, the four paths
Tests assert totals, not only no exception; then in game from the same build: full inventory, fastest repeat, source
dropped or banked mid-action, counts by `get_inventory` and `get_container_history`. A missing path, a test without
totals or a count off by one fails the row, naming the flow.
