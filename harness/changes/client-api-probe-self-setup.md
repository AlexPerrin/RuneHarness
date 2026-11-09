---
slug: client-api-probe-self-setup
track: client
priority: P2
goal: client-api
deps:
- h-mobile-login-page-39-again
---
# api-probe: the measure reaches every set-up-dependent instance by itself, on the slug's own fresh account

Measure at f7d94a7 (evidence/client-api/api-probe.tsv, 90.3%) runs tools/api-probe.sh with none of the manual set-up its header and client-state.md describe, now on the slug's own fresh account (h<sha>m: empty inventory, empty friends list). 38 rows that passed under the manual set-up read unreached/skipped/mismatch: ItemContainer 8 (getItemContainer(93) null: no items), Nameable 2 and ChatPlayer 1 (no friend listed), Hitsplat 3, GraphicsObject 10, HealthBarConfig 4 (no fight), Script 2 and PendingLogin 2 (probewait not set; no friend changes presence), WorldMapRegion 1 and WorldMapIcon 2 plus the setWorldMapPositionTarget mismatch (map not open), closeInterface skipped (no modal). At 91.0% (evidence/client-mobile-own-account-live) the tester account still had items and a friend.

Done when tools/api-probe.sh (or the probe plugin) builds that state itself before the rows run, with no human step: items given (::item), a friend added whose presence changes while the probe waits (a second client, e.g. the fork track's live-desktop the measure already knows), the fight on a lasting dummy with the scythe spotanim, a song, the world map, the skills tab and a modal, then cleans up what it spawned; track.sh measure on the mobile reports every one of those rows pass. The tester account's rules hold (never ::empty; drop only what was spawned).

## Client.stopNow
Also in scope: stopNow is skipped (it ends the client before the report). Have the probe write its report, then call stopNow last, and api-probe.sh confirm the app process ended (and restart it for down) to record the row's result; the row then passes on the mobile measure.
