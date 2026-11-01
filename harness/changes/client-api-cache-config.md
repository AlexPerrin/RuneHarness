---
slug: client-api-cache-config
track: client
kind: change
title: 'Cache indexes, node caches and config lookups (EntityOps, params, NPC overrides,
  DBRowConfig): 23 inert, unblocks 8'
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Cache, index and config lookups are ClientStub throws or Inert proxies. Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows (inert):
- Client: getIndex(I), getIndexConfig, getIndexScripts, getIndexSprites (Inert IndexDataBase), getDBRowConfig,
  getAnimationCache, getItemCompositionCache, getItemModelCache, getItemSpriteCache, getObjectCompositionCache,
  resetHealthBarCaches, getWidgetFlags, getVarcMap (13).
- IndexDataBase (Inert proxy): getFileIds, isOverlayOutdated, loadData (3).
- NPCComposition.getOps, ObjectComposition.getOps, ParamHolder.getParams (ItemCompositionStub) (3).
- NPC: getChatheadOverrides, getModelOverrides, getOverheadArchiveIds, getOverheadSpriteIds (4).
- Unblocks DBRowConfig 1, EntityOps 3, NpcOverrides 4 ("no live ... instance").
Implement them over the game's cache archives, node caches and config objects (loadData returns the real bytes of a
known archive/file; a cache getter returns the live NodeCache).
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
