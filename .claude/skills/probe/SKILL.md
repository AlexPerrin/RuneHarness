---
name: probe
description: "Find out what the test server does or sends, read-only: logs, packets, account data, gamevals and cache data. Use when a client feature depends on server behaviour, or to write a blocker's repro for a server change."
---
# Probe (read-only)

- Logs: `tracks/fork/track.sh log <slug> <pattern>` (a change's own server) or `log live <pattern>` (the live server).
- Packets: the desktop client's RSProx transcript of your own instance (`tracks/fork/track.sh recordings` for the official
  game's); the Android protocol notes in the client repo.
- Account data: the read-only SQL tool; gamevals and cache: `osrs-mcp` (`gameval_search`, `cache_search`).
- Game data: `osrs-mcp` (`wiki_search`, `wiki_page`, `wiki_npc_spawns`).

## A blocker (the client's dev files a server change)
`hd new <slug> --track server --title ... --goal client-api` with the repro on the test server, the expected behaviour
and its source, as a dep of the client change. Never a workaround in the client.
