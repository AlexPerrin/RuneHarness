---
slug: client-api-probe-setters
track: client
kind: change
title: 'api-probe: observe setters without a same-name getter, game-owned collection
  mutations and native hooks (53 skipped/unchecked rows)'
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Probe coverage, not a client gap: the probe skips or leaves unchecked methods whose effect is readable some other
way, and they count as not passing. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows:
- skipped "setter without a getter to read back and restore" (40): Client setAllWidgetsAreOpTargetable,
  setCameraMouseButtonMask, setCameraPitchRelaxerEnabled, setCameraSpeed, setCompass, setFreeCameraSpeed,
  setGeSearchResultCount/Ids/Index (native), setGpuFlags, setInventoryDragDelay, setInvertPitch, setInvertYaw,
  setLoginScreen, setMinimapTileDrawer, setOculusOrbNormalSpeed, setScalingFactor, setShouldRenderLoginScreenFire,
  setStretchedIntegerScaling, setStretchedKeepAspectRatio, setUnlockedFps, setUnlockedFpsTarget,
  setVarbitValue([III) (native); Actor.setActionFrame; ParamHolder setValue(II)/(IJ)/(ILString);
  PlayerComposition.setHash; widgets.Widget setForcedPosition, setSubOp and the 13 setOn*Listener(Object[])
  (native); worldmap.WorldMap.setWorldMapPositionTarget.
- skipped "mutates a game-owned collection, not restorable": Deque addLast/clear, IterableHashTable.put (3): run them
  on a probe-owned collection (Client.createDeque / a fresh table) instead.
- unchecked "native hook; its effect is not readable through the API" (10): Client playSoundEffect x4,
  queueChangedSkill, queueChangedVarp, refreshChat; ChatLineBuffer.removeMessageNode; Widget revalidate,
  revalidateScroll: read the effect through the event the hook raises (SoundEffectPlayed, StatChanged,
  VarbitChanged, the chat buffer's line count, widget bounds) or the host's native state.
For each, check through the matching getter under another name (ParamHolder.getIntValue/getStringValue,
getVarbitValue(int[],int), Widget.getOn*Listener, ...), the event it raises, or host/native state; restore after.
Only a row whose effect the probe now observes may pass; a method the client really does not implement becomes
inert/mismatch, not pass.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on the dev's own client instance on the test server: none of
  the rows above is `skipped` or `unchecked`; each is pass with the observed effect as evidence, or a real
  inert/throw/mismatch.
- No baseline pass row changes result; the hand-over quotes the new percentage and the result diff.
- The device is restored and the probe jar removed (device-test).
