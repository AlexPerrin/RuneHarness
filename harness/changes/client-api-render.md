---
slug: client-api-render
track: client
kind: change
title: 'Client and WorldView rendering surface: rasterizer, textures, buffer provider,
  projections, camera focal point (29 inert, unblocks 37 rows)'
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
The client's rendering surface is ClientStub/WorldViewStub throws. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows (inert):
- Client: getRasterizer, getRasterizer3D_clipMidX2/MidY2/NegativeMidX/NegativeMidY, getTextureProvider,
  getBufferProvider, getCameraFocalPointX/Y/Z and setCameraFocalPointX/Y/Z, getDraw2DMask/setDraw2DMask,
  getSkyboxColor/setSkyboxColor, getDrawCallbacks/setDrawCallbacks, invalidateStretching, setStretchedEnabled,
  setStretchedFast, getCrossSprites, getMapIcons, getMapScene (27).
- WorldView: getCanvasProjection, getMainWorldProjection (2).
- Unblocks, all "no live ... instance": Rasterizer 9, Texture 8, TextureProvider 5, BufferProvider 3,
  MainBufferProvider 1, IntProjection 7, Projection 2, FloatProjection 1, and Client 1 ("no live Projection for an
  argument") (37 rows).
Implement them over the Android client's renderer state; where the Android renderer has no equivalent of a desktop
concept (stretched mode, a DrawCallbacks GPU hook), the method must still return the declared type with the client's
real state and the hand-over says what the value means on Android.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
