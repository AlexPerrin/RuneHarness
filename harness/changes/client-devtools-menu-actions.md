---
slug: client-devtools-menu-actions
track: client
kind: change
title: Devtools menu actions do nothing on current builds (item_action, select_option,
  widget ops time out in the host's DevMenu)
priority: P2
deps: [harness-device-network-block]
created: '2026-10-25T22:12:13Z'
---
## Change
Two client agents (client-api-probe-reach-2 at 88861bf, client-api-projectile-2 at 4ad967d) found that the osrs-devtools actions that drive the game time out in the host: `item_action` (Wield, Drop), `select_option` and widget ops (host `DevMenu`). Reads still work. Agents fell back to taps placed from widget bounds. Find why the host's menu dispatch no longer completes and fix it.

## Definition of done
- On a build at the change head, on your own Agent_Phone emulator logged in on the test server: `item_action` Wield and Drop on an inventory item, `select_option` on a dialogue and one widget op each take effect, confirmed by the matching read (get_inventory, the dialogue state, the widget state), recorded in the evidence.
- The api-probe report shows no row lost against main's (evidence/client-api-projectile/api-probe.tsv once merged).

## Answers
- 2026-10-31T01:30:14Z Contact logged in docs/ISSUES.md. Resume: build with OPENRUNE=1 LOCAL_AUTH=1 tools/repack.sh and check the repack log has the RSA/jav_config/appauth patched lines before installing.
