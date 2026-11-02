---
slug: harness-deploy-survives-tools-ship
track: harness
title: a tools ship kills an in-flight deploy of the same tree; its cache download
  restarts from zero
kind: change
priority: P0
mechanism: build-gate
deps: []
created: '2026-11-02T02:53:48Z'
---
sweep-26 P0-a: live ship 6bf30c2 stopped 02:12:03Z ~30% into :or-cache:freshCache; e67816036 stopped 02:51:37Z ~47% in, args and tree unchanged, only the key suffix moved (8c23c2d55eca -> 3884518f40b0, the e86869f tools ship); the restart downloads the 213 MB cache from 0 (state/integration/build-e6781603613b...-2.log). The store g-<GK> (build.sh ~line 70) is written only after a completed download, so or-cache-store holds no g-*; live has not deployed since 23:13Z. Key a deploy by the tools files it runs, never stop an in-flight build of the same tree, and keep a partial/complete download across restarts. evidence/monitor/sweep-26.md

Also (filed): a build keeps an old game.yml: build.sh copies game.example.yml only when game.yml is missing
server-token-auth-17 (qa): build.sh line 49 copies game.example.yml to the build copy's game.yml only when game.yml is missing, so images keep an old game.yml: or:2cdbf708b's /app/game.yml still has the old RS256 token-login comment while T has the auth type 2 text (comments only, no row affected). A build renders game.yml from T's game.example.yml every time. Evidence: evidence/server-token-auth/qa17-ingame.txt
