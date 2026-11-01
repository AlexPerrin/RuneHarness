---
slug: client-api-projectile
track: client
kind: change
title: createProjectile on Client and WorldView, and the probe reaching the Projectile
  it creates (3 inert, 26 unreached)
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Projectile creation is a ClientStub/WorldViewStub throw, and the probe never reaches a Projectile. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows:
- inert Client.createProjectile (both overloads), WorldView.createProjectile (3).
- unreached Projectile (26 rows "no live Projectile instance"): with createProjectile working the probe creates one
  (or reads WorldView.getProjectiles) and calls the 26 methods on it.
Implement createProjectile over the game's projectile spawn so the projectile is drawn and listed in
WorldView.getProjectiles; extend tools/api-probe.sh (host/plugins/api-probe) to reach the instance it creates.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
