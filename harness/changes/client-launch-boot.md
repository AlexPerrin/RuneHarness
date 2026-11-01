---
slug: client-launch-boot
track: harness
title: 'up: emulator boots from a snapshot instead of cold'
kind: change
priority: P0
goal: client-launch
units:
- launch:boot
created: '2026-11-01T01:01:19Z'
deps: [harness-device-network-block, harness-no-powershell, client-launch-measure]
---
Each up cold-boots Agent_Phone (-read-only, -gpu swiftshader_indirect, up.ps1:29) and polls sys.boot_completed every 2 s (up.ps1:31). Boot from a saved snapshot per instance (read-only base kept, so instances stay parallel and unlocked) and use host GPU where the emulator offers it; wait for boot on the fact (adb wait-for-device then getprop sys.boot_completed in one blocking shell loop on the device, or the boot_completed broadcast), not a host-side fixed poll. Proof: client-launch report's boot step shorter than the measured cold boot, same device state (backup and restore on down unchanged). Marks launch:boot.
