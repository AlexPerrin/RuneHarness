---
slug: client-api-probe-effects
track: client
kind: change
title: 'api-probe: observe and undo session-ending and server-visible methods (world
  hop, game state, menuAction, runScript; 21 skipped rows)'
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Probe coverage, not a client gap: session-ending or server-visible methods are skipped. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows (skipped, 21):
Client changeWorld, hopToWorld, openWorldHopper ("world hop ends the session"), setGameState (native), stopNow,
changeMemoryMode, menuAction (native), runScript (native), openInterface, closeInterface (native), setUsername,
setPassword, setOtp ("login credential field"); GameEngine initialize, resizeCanvas, setConfiguration,
unblockStartup ("applet lifecycle"); Scene removeGameObject, removeTile; ScriptEvent.run.
Call each where the probe can observe and undo it, as a last phase of the probe: hop to the test server's own world
and log back in, a menuAction walk onto the player's own tile, a runScript of a client-only script, open then close a
client-side interface, set the login fields on the login screen and clear them, remove then re-add a probe-spawned
scene object, resizeCanvas and check the canvas size. Methods that stay unobservable keep "skipped" with the reason.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on the dev's own client instance on the test server ends
  logged in on the same world with the account unchanged, and each row above is pass with the observed effect, a
  real inert/throw/mismatch, or skipped with a reason the hand-over justifies.
- No baseline pass row changes result; the hand-over quotes the new percentage and the result diff.
- No connection other than the test server (network-qa expected hosts); device restored, probe jar removed.
