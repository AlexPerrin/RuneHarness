---
slug: client-api-probe-reach
track: client
kind: change
title: 'api-probe: set up the game state that reaches unreached interfaces (combat
  effects, clan/FC, world entities, UI nodes; 79 rows)'
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Probe coverage, not a client gap: instances the probe never reaches because the game state that creates them is
not set up. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows (unreached, "no live ... instance" unless noted):
- Combat and effects: GraphicsObject 10, Hitsplat 3, HealthBarConfig 4, DynamicObject 5 (fight a test-server NPC,
  stand by an animated object).
- Social: clan.ClanSettings 4, ClanChannel 3, ClanChannelMember 3, ClanMember 3, FriendsChatManager 4,
  FriendsChatMember 2 (join a clan / friends chat on the test server).
- WorldEntity 9, WorldEntityConfig 6 (a world entity, e.g. a boat, in the scene).
- UI and misc: Script 2, widgets.WidgetConfigNode 2, worldmap.WorldMapIcon 2, worldmap.WorldMapRegion 1,
  FontTypeFace 3, ColorTextureOverride 2, IntegerNode 2, PendingLogin 2, ClientConfiguration 3.
- Arguments: Actor and TileObject ("no live java.awt.Graphics2D for an argument"), SpritePixels ("no live
  java.awt.Color for an argument"): give the probe a host Graphics2D/Color.
Extend host/plugins/api-probe and tools/api-probe.sh to set up that state (only with items it spawns, never touching
the tester's items or GE offer) and reach each instance. Where the test server cannot produce the state (clan, a
world entity), the hand-over names the missing server behaviour so a server change can be filed; those rows stay
unreached.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on the dev's own client instance on the test server: every
  interface above is reached (its rows pass or show a real inert/throw/mismatch), except the ones the hand-over
  names with the missing server behaviour.
- No baseline pass row changes result; the hand-over quotes the new percentage and the result diff.
- The account and device are restored and the probe jar removed (device-test).
