---
slug: harness-jav-config-local-only
track: harness
title: Every served jav_config names only local hosts
kind: change
priority: P0
deps: []
created: '2026-10-31T23:56:00Z'
---
From the qa run server-sidecar-jav-config-local-auth-1 (evidence/server-sidecar-jav-config-local-auth/accuracy.md: the non-local hosts per line, what each sidecar serves today, 4 rules). The served jav_config comes from sidecar image osrs-rsps-test:241 and from local/harness. track.sh up seds out the jagex/runescape URLs for branch servers but keeps param 19's Google client id and garbles msg=tandc; the live compose's http and http-desktop serve the image template unchanged. Fix on local/harness: one rewritten template mounted by track.sh up and by the compose's http and http-desktop, and a tools/server check (fetch the served config, fail on any non-local host) run by up and by the client network QA. Then the server change server-sidecar-jav-config-local-auth is dropped (the user's word). Privacy rule: no client ever contacts Jagex or RuneScape servers. One test per requirement touched.
