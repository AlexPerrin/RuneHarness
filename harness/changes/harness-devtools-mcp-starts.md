---
slug: harness-devtools-mcp-starts
track: harness
title: The devtools MCP servers fail to start in every session
kind: change
priority: P1
deps: []
created: '2026-11-01T02:31:32Z'
---
Every session's osrs-devtools-mobile and osrs-devtools-desktop MCP servers fail with CONNECTION_CLOSED, so agents fall back to the client's HTTP endpoint (port 7783) against the shared rule 'testing tools over screenshots' through the MCP data tools. Evidence: server-friends-chat-clan-channels-6 last line 'the osrs-devtools-desktop and osrs-devtools-mobile MCP servers failed to connect in this session too (CONNECTION_CLOSED)'; goblin-diplomacy-review-367-fftgsrq-4 'The osrs-devtools-desktop MCP server failed to connect this run'; client-loading-fullscreen-rotate-2 'The devtools MCP servers also failed to connect in this session'; orchestrator-16 saw the same at spawn. Cause found: running '/home/alex/osrs-harness/mcp/devtools_bridge.py desktop ...' with an initialize request exits 1 with FileNotFoundError: mcp/devtools-snapshot.json (deleted in e939a3b, the v8 skeleton; the bridge loads it at import). The desktop backend in .mcp.json, /home/alex/osrs-harness/bench/multiclient/desktop-devtools-mcp.sh, was also removed (bench/ gone). Make both servers start with no client running (restore or drop the snapshot fallback; point the desktop entry at the live desktop devtools backend of the bring-up script), so tools/list answers and a call reaches a running client. Proof: a fresh session lists the osrs-devtools-desktop tools and get_client_state answers against an up desktop client. One test per requirement touched.
