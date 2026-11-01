---
slug: harness-immersive-confirm
track: harness
title: Bring-up accepts the 'Viewing full screen' prompt with no tap
kind: change
priority: P1
deps:
- harness-device-network-block
goal: client-launch
units: [launch:loading-fullscreen]
created: '2026-11-01T01:28:16Z'
---
The user's word: file it as harness and close client-loading-fullscreen-rotate. The 'Viewing full screen / Got it' prompt is SystemUI's immersive-mode confirmation. The app cannot confirm it (WRITE_SECURE_SETTINGS needs adb or a privileged app). In the client track's boot, before the app launches: adb shell settings put secure immersive_mode_confirmations confirmed. Drop 'Got it' from tools/device_login.py's tapped LABELS. No tap and no added wait (launch optimization). Rotation needs nothing: the user says it is fine; rotate left = counter-clockwise to landscape, rotate right back to portrait. On client/harness-v8. Device proof after harness-device-network-block ships: the prompt never shows at launch. One test per requirement touched.
