---
slug: client-api-client-state
track: client
kind: change
title: 'Client session, settings and menu state: 35 ClientStub throws and 6 setters
  that do not take'
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Client session, settings and menu state are ClientStub throws or setters that do not take. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows:
- inert Client: getAccountType, getBuildID, getCallbacks, getCrossWorldMessageIds, getCrossWorldMessageIdsIndex,
  getCurrentLoginField, getLoginIndex, getMusicVolume/setMusicVolume, getOculusOrbFocalPointX/Y, setOculusOrbState,
  setCameraMode, setCameraShakeDisabled, getServerVarpLongValue, getServerVarpsLong, getVarpLongValue,
  getVarpsLong, setVarpLongValue, getSocketFD, getWorldHost, getWorldList, isMouseoverTextEnabled/
  setMouseoverTextEnabled, setExpandedMapLoading, setMenuScroll, setTickCount, getActiveMidiRequests,
  getAnimationInterpolationFilter/setAnimationInterpolationFilter, draw2010Menu, drawOriginalMenu (34);
  WorldView.getYellowClickAction.
- mismatch (setter does not take): Client.setIdleTimeout (native; "15000 -> set 14999 -> 15000"),
  Client.setMenuEntries and Menu.setMenuEntries ("MenuEntry[2] -> set MenuEntry[2] -> MenuEntry[2]": the probe sets
  a different array, the getter returns the old one), Client.setMinimapZoom(D) ("4.0 -> set 5.0 -> 4.0"),
  Client.setMinimapZoom(Z), Client.setWidgetSelected (native) (6).
- Unblocks MidiRequest (2 rows) through getActiveMidiRequests.
getSocketFD and getWorldHost must report the test server connection only (privacy rule: nothing reaches Jagex).
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
