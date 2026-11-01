---
slug: harness-jav-config-reland
track: harness
title: Re-land the jav_config local-only fix on the fork's tools branch
kind: change
priority: P0
deps:
- harness-ship-tools-atomic
created: '2026-11-01T00:34:12Z'
closed: 'answer-1: The user closed this re-land: the original change harness-jav-config-local-only finishes the fork side.'
---
harness-jav-config-local-only reads done, but its ship only partly landed (orchestrator-1). v8 and client/harness-v8 (90ad1f9a0) moved. The fork's local/harness fast-forward to 5b2fddddc failed with 'Not possible to fast-forward', and 5b2fddddc is still not an ancestor of local/harness (tip 97b61e64f). So the template mounted by up, the compose sidecars and javcheck.py are not live on the test server's tools branch. Privacy rule: no client contacts Jagex or RuneScape servers. Carry the fork commits from harness/harness-jav-config-local-only, merged onto the current local/harness with no .pyc files, and ship them with the atomic tools ship. Prove it: javcheck passes against a served jav_config. One test per requirement touched.
