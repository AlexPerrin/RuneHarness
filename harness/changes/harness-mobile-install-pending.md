---
slug: harness-mobile-install-pending
track: harness
title: Mobile up fails the APK install on a pending install request
kind: change
priority: P1
deps: []
created: '2026-11-01T03:27:14Z'
---
client-login-index-log-1 (2026-11-01T03:14:25Z), after harness-device-boot-failure-cleanup shipped (done 01:25:35Z), still hit on up:
install failed: ... Failure [INSTALL_FAILED_DUPLICATE_PACKAGE: Scanning Failed.: Duplicate package com.jagex.oldscape.android in pending install requests.]
RESTORE FAILED: plugins dir is not the three defaults
cat: state/client-login-index-log/serial: No such file or directory
The run's up took its own emulator down; a manual retry worked. The step is the client tools branch's tools/track.sh:82-83 (uninstall, then install -r, no check that the package manager is idle). Make up's install succeed on the first try: install only once the device reports its package manager ready and no install of the package is pending on that serial, and act on that observed fact, no sleep or retry count. On a failed install, down/restore must not report a plugins-dir restore failure for an app that was never installed. Fix on the client's client/harness-v8 tools branch (carried head); tools/test_track.py covers it.
