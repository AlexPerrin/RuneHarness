---
slug: client-launch-host-start
track: client
title: 'host start: plugins loaded off the launch path''s critical steps'
kind: change
priority: P3
goal: client-launch
units:
- launch:host-start
created: '2026-11-01T01:01:19Z'
deps: [harness-device-network-block, client-launch-measure]
---
From logcat ActivityTaskManager START of the app to osrsrl-host 'host ready; N plugin(s) running' (Host.java:143-265) the host loads every plugin before the client proceeds. Read the client-launch report's host-start step; whatever the host does there that the login screen does not need (plugin class loading, the devtools httpserver start) runs after or alongside the client's own start, so the step adds nothing measurable over the app without plugins. Proof: report's host-start step against one launch of the same APK with no plugins pushed. Marks launch:host-start.
