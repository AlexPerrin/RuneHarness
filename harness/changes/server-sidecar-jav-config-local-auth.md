---
slug: server-sidecar-jav-config-local-auth
track: server
kind: local
title: jav_config served to the desktop clients names Jagex auth and account hosts
priority: P0
deps: [harness-jav-config-local-only, harness-close-done]
created: '2026-10-31T20:04:18Z'
---
Privacy (A10: no client ever contacts Jagex). The branch server's HTTP sidecar (image osrs-rsps-test:241, server-tools/sidecar, container qa-or-http-<owner>, served on 127.0.0.1:<http port>/jav_config.ws to the desktop clients through RSProx) lists https://account.jagex.com/, https://auth.jagex.com/, https://social.auth.jagex.com/, https://auth.runescape.com/, http://oldschool.runescape.com/, the Jagex legal pages and a Google OAuth client id; only the game and config endpoints are local. Seen 2026-10-31 on qa-or-http-scc2 (curl -s http://127.0.0.1:8092/jav_config.ws). No contact found in that day's RSProx logs, but the client's Jagex-account path (the account upsell that bench/multiclient/desktop.sh login dismisses with fixed-mode clicks, which land ~15/22 px off in resized clients) would follow them. The hosts are not in the server tree; the sidecar app generates them. Repro: start a branch server with qa.sh start, then curl its jav_config.ws and grep for jagex/runescape/googleusercontent.

## Definition of done
- The jav_config served by every sidecar (branch servers and the live test server) names no Jagex, RuneScape or Google host: each such param is rewritten to a local endpoint or removed, the way OPENRUNE=1 LOCAL_AUTH=1 does for the APK.
- A check that fails when the served jav_config names any non-local host (curl + grep), run where the sidecar is built and by the client network QA.
- The desktop client still loads and logs in against a branch server after the change.
