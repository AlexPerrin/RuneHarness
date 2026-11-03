---
slug: harness-mobile-desktop-naming
track: harness
title: Name every client mobile or desktop
kind: change
priority: P1
deps: []
created: '2026-11-01T03:12:38Z'
---
The user's word: clearly split the clients by mobile and desktop in naming. Today the Android side is called device (device_login.py, harness-device-*, 'device' in docs), emulator or client, and the PC side desktop, desktopN or client. Use exactly two words everywhere: mobile (the official Android app on the emulator, client track) and desktop (RuneLite on Windows, server track's test clients). Rename scripts (device_login.py -> mobile_login.py), state keys and up.json fields, track.sh verbs and log lines, docs (PROBLEM, PRD, ARCHITECTURE, track.md), and the MCP entries (osrs-devtools-mobile and osrs-devtools-desktop already follow it). Future change slugs use harness-mobile-* and harness-desktop-*. Existing change slugs are not renamed. One test per requirement touched.
