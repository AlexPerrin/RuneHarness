---
slug: client-api-actor-anim
track: client
kind: change
title: Actor and Player animation, pose and spot anims instead of PlayerStub throws
  (29 inert, 1 mismatch, unblocks ActorSpotAnim)
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Actor/Player animation, pose and spot-anim state are generated PlayerStub throws ("Player.X is not implemented on
Android yet"). Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows (inert unless noted):
- Actor: clearSpotAnims, createSpotAnim(IIII), getGraphicHeight, getSpotAnimFrame, removeSpotAnim, setAnimation,
  setAnimationFrame, setDead, setGraphic, setGraphicHeight, setIdlePoseAnimation, setIdleRotateLeft/Right,
  setPoseAnimation, setPoseAnimationFrame, setRunAnimation, setSpotAnimFrame, setWalkAnimation, setWalkRotate180,
  setWalkRotateLeft/Right (21).
- Player.setSkullIcon; Renderable getModelHeight, getRenderMode, setModelHeight; Node getHash, getNext, getPrevious on
  Player (7).
- mismatch Actor.setOverheadText: "getOverheadText null -> set \"api-probe\" -> null".
- Unblocks ActorSpotAnim (10 rows "no live ActorSpotAnim instance"): Actor.getSpotAnims must return the live spot anims
  so the probe reaches one (createSpotAnim on the local player gives it one).
Implement them on the host's Actor/Player/NPC backing over the game's actor fields (native hooks where a setter must
write game state), so set-then-get round trips and the client shows the effect.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).

## Answers
- 2026-10-25T18:56:39Z console 2026-10-25: resume. On a fresh read-only AVD, adb uninstall com.jagex.oldscape.android first, install the repack, stop on any install error, launch only after libosrsrl.so is in the installed APK (skill test-instances, rule added in d07e9d9). Then run the probe on the merged build d4cb757 and hand over.
