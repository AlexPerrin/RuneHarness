---
slug: client-api-widget-fields
track: client
kind: change
title: Widget content type, drag parent, target priority, type and item quantity on
  the game widget instead of WidgetBag (8 rows)
priority: P1
deps: [harness-device-network-block]
created: '2026-10-25T15:48:53Z'
goal: client-api
---
## Change
Widget fields served by the host's WidgetBag instead of the game widget, and one native setter that does not take.
Report: ~/osrs-harness/evidence/client-api/api-probe.tsv (client-api 60.9%, pass 765/1256, live tip aba2ced00, build v0.1.1-48-g40adf4db7f15). Rows:
- inert (WidgetBag): getContentType/setContentType, getDragParent/setDragParent, getTargetPriority/
  setTargetPriority, setType ("mismatch: getType 0 -> set 1 -> 0") (7).
- mismatch widgets.Widget.setItemQuantity (native): "getItemQuantity 0 -> set 1 -> 0".
Back them with the game widget's fields so set-then-get round trips on a live widget.
## Definition of done
- `tools/api-probe.sh ~/osrs-harness/evidence/<slug>/` on a build at the change head, on the dev's own client instance
  logged in on the test server (skills device-test, test-instances), shows every row listed above as `pass`, with
  evidence that is a live value or an observed round trip/effect, not a *Stub, *Bag or Inert path.
- No row that is `pass` in the baseline report is anything else in the new report; the hand-over quotes the new
  percentage and the diff of results against the baseline.
- The device is restored and the probe jar removed (device-test).
