---
slug: client-api-widget-listeners
track: client
priority: P2
goal: client-api
deps:
- h-client-up-am-start-default
---
# Widget's 8 STORED listeners are kept but never run on Android

evidence/client-api/api-probe.tsv (90.3%): setOnClickListener, setOnHoldListener, setOnReleaseListener, setOnMouseOverListener, setOnMouseLeaveListener, setOnMouseRepeatListener, setOnScrollWheelListener and setOnDialogAbortListener on child 601:0[0] read 'stored as STORED (kept, never run: no host event runs a STORED listener)'. Desktop runs them from the game's widget event dispatch (op click, hold, release, hover enter/leave/repeat, scroll, dialog abort). Done when the host hooks the Android game's dispatch for each event (Ghidra; touch maps click/hold/release, the hover and scroll kinds to the game's own events where it raises them) and runs the plugin's listener, the probe triggers each and sees it run, and the 8 rows pass on the mobile measure.
