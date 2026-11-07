---
slug: client-probe-no-stop
track: client
priority: P2
goal: client-api
deps:
- h-mobile-login-pages
- local-android-rsprot-token-gjstr
- server-android-token-login
---
# api-probe: skip Client.stopNow and other client-ending methods; they stopped the RuneLite desktop before the report

## run 39: fix verified on desktop; mobile criteria wait on server-android-token-login
dd3d04d (pushed origin/client/client-probe-no-stop) skips Client.stopNow, the only client-ending method in runelite-api-1.13.1 (hopToWorld/openWorldHopper/changeWorld keep the session; setGameState is LAST). measure-desktop at dd3d04d wrote its report: stopNow skipped, 1093/1253 = 87.2% (evidence/client-probe-no-stop/api-probe-desktop.tsv; '# build: ?' on desktop, so it cannot pass check-probe). up fails at LoginIndex 3 after Play Now (the token refusal of server-android-token-login), so mobile-evidence, probe and state-doc wait on it: once it lands, up, tools/api-probe.sh in the build copy, client-state.md's result line, then submit.
