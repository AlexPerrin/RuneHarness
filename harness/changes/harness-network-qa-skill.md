---
slug: harness-network-qa-skill
track: harness
title: network-qa skill allows the local server and the two RuneLite hosts only
kind: change
priority: P1
deps: []
created: '2026-11-01T03:39:01Z'
---
client/harness-v8 .claude/skills/network-qa/SKILL.md lists api.runelite.net, static.runelite.net, Braze, OneTrust and Google as allowed hosts. The user's word: the client may contact the local server (10.0.2.2), api.runelite.net and static.runelite.net (plugin data); telemetry stays blocked. Make the skill's allowed list exactly those three; any telemetry host (Braze, OneTrust, Google analytics/Firebase, Singular, any Jagex or RuneScape host) or any other host is a FAIL. One test per requirement touched.
