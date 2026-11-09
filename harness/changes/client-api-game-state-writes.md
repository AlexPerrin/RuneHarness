---
slug: client-api-game-state-writes
track: client
priority: P2
goal: client-api
---
# Game-state writes with no effect on Android: openInterface, setAllWidgetsAreOpTargetable, Scene.removeGameObject/removeTile, PlayerComposition.setHash, Widget.setForcedPosition, setInventoryDragDelay

evidence/client-api/api-probe.tsv (90.3%): openInterface is a ClientStub throw; Scene.removeGameObject and removeTile are SceneStub throws; setAllWidgetsAreOpTargetable, PlayerComposition.setHash and WidgetBag's Widget.setForcedPosition change no field and make no native call (inert); setInventoryDragDelay(16) leaves inventory 149:0[0]'s drag dead time at 6 (mismatch). Each writes the game's own state (Ghidra, offsets.md) as desktop's mixins do: open the sub-interface into the game's interface table, the global op-targetable flag, the scene tile and loc removal, the composition hash, the widget's forced position, the inventory items' drag dead time. Done when those 7 rows pass on the mobile measure with no pass lost.
