---
slug: client-api-model
track: client
kind: change
title: Model, ModelData and Mesh backed by the game's models instead of ModelBag/InertModelData
  (61 inert rows, unblocks AABB)
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Model, ModelData and Mesh resolve to the host's ModelBag / ModelDataBag / InertModelData: every call "passes" with 0,
empty arrays or another bag, so the probe marks them inert. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows:
- Model (35): calculateBoundsCylinder, calculateExtreme, drawFrustum, drawOrtho, getAABB, getBottomY, getBufferOffset,
  getDiameter, getFaceBias, getFaceColors1/2/3, getFaceRenderPriorities, getOverrideAmount/Hue/Luminance/Saturation,
  getRadius, getSceneId, getTexIndices1/2/3, getTextureFaces, getTransparency, getUnlitFaceColors, getUnskewedModel,
  getUvBufferOffset, getVertexNormalsX/Y/Z, getXYZMag, setBufferOffset, setSceneId, setUvBufferOffset, useBoundingBox.
- Mesh (15): getFaceCount, getFaceIndices1/2/3, getFaceTextures, getFaceTransparencies, getVerticesCount,
  getVerticesX/Y/Z, rotateY90/180/270Ccw, scale, translate.
- ModelData (11): cloneColors, cloneTextures, cloneTransparencies(), cloneTransparencies(Z), cloneVertices,
  getFaceColors, light(), light(IIIII), recolor, retexture, shallowCopy.
- Client.applyTransformations (ClientStub throw).
- Unblocks AABB (6 rows "no live AABB instance") through Model.getAABB.
Back Model/ModelData/Mesh with the game's model objects (the ones Renderable.getModel, Client.loadModel and
loadModelData return), so values are the real geometry (non-zero vertex counts for a loaded NPC or player model).
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
