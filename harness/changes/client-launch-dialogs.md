---
slug: client-launch-dialogs
deps: [harness-device-network-block]
track: client
title: no first-run dialogs at launch (Got it, Stay signed out, Accept, No thanks)
kind: change
priority: P2
deps:
- client-launch-measure
goal: client-launch
units:
- launch:dialogs
created: '2026-11-01T01:01:19Z'
---
device_login.py's tap_label runs uiautomator dump (1-2 s each) and taps the first of 'Got it', 'Stay signed out', 'Close', 'Accept', 'No thanks' on every LOGIN_SCREEN pass. Find which component shows each dialog (the app's prefs, the com.jagex.mobilesdk activity) and remove them at the source: the state they record as dismissed seeded at up, or the host/telemetry patch skipping them, so launch goes to the login screen with none shown. No call to Jagex servers in any case (privacy rule). Proof: client-launch report shows no dialog step and logcat shows no mobilesdk activity start. Marks launch:dialogs.
