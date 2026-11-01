---
slug: client-api-scene-tile
track: client
kind: change
title: Scene terrain data and Tile scene tile model/paint (17 inert, unblocks SceneTileModel
  and SceneTilePaint, 39 rows)
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Scene and Tile terrain data are SceneStub/TileStub throws. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows (inert):
- Scene (12): getDrawDistance, setDrawDistance, getMinLevel, setMinLevel, getOverlayIds, getUnderlayIds,
  getTileShapes, getOverrideAmount/Hue/Luminance/Saturation, getSkybox.
- Tile (4): getSceneTileModel, setSceneTileModel, getSceneTilePaint, setSceneTilePaint.
- Client.createSceneTilePaint(IIIIIIZ).
- Unblocks SceneTileModel (21 rows) and SceneTilePaint (18 rows), all "no live ... instance", through the Tile getters.
Implement them over the game's scene and tile structures; the setters round trip (restored after).
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
