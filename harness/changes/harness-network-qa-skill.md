---
slug: harness-network-qa-skill
track: harness
title: network-qa skill allows only the local server
kind: change
priority: P1
deps: []
created: '2026-11-01T03:39:01Z'
---
client/harness-v8 .claude/skills/network-qa/SKILL.md still lists api.runelite.net, static.runelite.net, Braze, OneTrust and Google as allowed hosts. Since client-host-runelite-fetches the host contacts 10.0.2.2 only and privacy says no client contacts Jagex or RuneScape. Make the skill's allowed list the local server alone; any other host is a FAIL. One test per requirement touched.
