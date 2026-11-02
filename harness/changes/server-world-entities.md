---
slug: server-world-entities
track: server
kind: local
title: 'World entities: the server never creates one (no boat or other world entity
  in any scene)'
priority: P2
created: '2026-10-25T20:31:36Z'
goal: client-api
deps:
- harness-server-build-tree
- harness-no-powershell
- harness-server-build-musicrepository
- harness-desktop-first-login
- harness-joined-finding-not-users-answer
---
Blocks the client-api probe's WorldEntity (9) and WorldEntityConfig (6) rows (client change client-api-probe-reach): WorldView.worldEntities() is always empty in the Android host, so they stay unreached.

Repro on the test server: anywhere in the world, WorldView.worldEntities() on the top-level world view is empty; no content spawns one. Source: in the fork, RegionRegistry.registerWorldEntity() has no caller, the WorldEntityInfo supplier (api/net rsprot/provider/WorldEntityProvider.kt) never gets an avatar, and there is no Sailing content.

Expected (official): world entities (Sailing boats, and the other world-entity content since 2025) are sent through WORLDENTITY_INFO with their own world view; the client builds a WorldEntity with its config (bounds, category, id). Minimum to unblock the client: one world entity (e.g. a boat) spawned in a scene the tester can reach.

## Answers
- 2026-10-31T01:30:52Z (c) plus (a): a minimal test-only local/* branch now (one static world entity, e.g. a raft near Port Sarim, sent through WORLDENTITY_INFO, no riding or steering) that never goes upstream, to unblock client-api-probe-reach; for upstream, wait for #182.
