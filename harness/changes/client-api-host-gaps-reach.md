---
slug: client-api-host-gaps-reach
track: client
kind: change
title: 'Host gaps behind unreached probe rows: DynamicObject, HealthBarConfig, Script,
  ColorTextureOverride, PendingLogin (host never creates them)'
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T20:46:12Z'
goal: client-api
---
Found by client-api-probe-reach: these rows stay unreached on any game state because the Android host never hands out an instance (not a probe-coverage problem).
- DynamicObject 5: GameObject/WallObject/DecorativeObject.getRenderable*() always return null (host AndroidTileObject), so an animated loc never yields a DynamicObject. Needs the game's animated loc renderable (sequence, frame, cycle, model).
- HealthBarConfig 4: the host never posts PostHealthBarConfig (the only API path to a HealthBarConfig). Needs the game's health bar type (front/back sprites, padding) and the event.
- Script 2: ScriptCallbackEvent is posted without a Script (host ScriptCallbacks.post sets only the event name). Needs the running script's instructions and int operands.
- ColorTextureOverride 2: AndroidPlayerComposition get/create/getColorTextureOverride(s) return null. Needs the appearance block's per-kit recolour/retexture overrides.
- PendingLogin 2: FriendContainer.getPendingLogins() is a permanently empty deque (host AndroidNameables). Needs the game's pending friend login/logout notices (a friend logging in on the test server).
- FontTypeFace.getBaseline / drawWidgetText now reached and throw UnsupportedOperationException (host GameFont).
Once the host produces them, the probe needs @Subscribe for PostHealthBarConfig and ScriptCallbackEvent to register the instance (host/plugins/api-probe; the HitsplatApplied/GraphicsObjectCreated handlers are the pattern). Baseline report: ~/osrs-harness/evidence/client-api-probe-reach/api-probe.tsv.
