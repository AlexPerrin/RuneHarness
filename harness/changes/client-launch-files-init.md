---
slug: client-launch-files-init
track: harness
mechanism: mobile
title: 'up: no throwaway first app start and fixed sleep to create files/'
kind: change
priority: P1
goal: client-launch
units:
- launch:files-init
created: '2026-11-01T01:01:19Z'
deps: [harness-device-network-block, harness-no-powershell, client-launch-measure]
---
up.ps1:37 (moved to bash by harness-no-powershell) starts the app with monkey, sleeps a fixed 5 s, and force-stops it, only so files/ exists before the plugins are pushed. A fixed sleep breaks the atomic rule and the extra start lengthens every launch. Create the plugin and devtools directories directly (adb shell run-as mkdir -p) or, if the app must create them, wait on the fact (the directory exists, or the host's 'host starting' line) and stop at once. Proof: the client-launch report shows no files-init step, and the plugins load at the first real start (logcat 'host ready; N plugin(s) running'). Marks launch:files-init.
