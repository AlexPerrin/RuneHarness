---
slug: harness-script-end-is-result
track: harness
title: A script that exits 0 has ended with its result; start() counts only failed
  exits
kind: change
priority: P0
mechanism: loop
deps: []
created: '2026-11-02T19:05:10Z'
---
Root cause (PRD R5, a track script runs once per key and its failure is raised): start() (hd.py ~1310-1340) takes a script's result to be state/<slug>/<name>.json newer than its proc record, and a script that left none as a death. Two scripts end successfully without that file: the harness ship writes state/ship-harness/shipped (tools/track.sh kept()) and drops proc-ship.json only on its two early exits, not on the full ship; the server live ship writes state/live/tree.json. So each successful ship counts as a death, and because every success ends on the same last line, the cause rule (same cause across args) keeps the count across different heads until three successful ships raise the alert.

Evidence:
- alert: 'ship-harness: ship ended 3 times without a result since 2026-11-02T18:37:56Z (state/ship-harness/ship.log)' (planner-34). state/ship-harness/proc-ship.json: attempts 3, cause 'v8 at', args ship ship-harness 30f817386; ship.log ends 'v8 at e27c298', 'v8 at 30f8173' (both landed: git log shows e27c298 and 30f8173 on v8). No state/ship-harness/ship.json exists.
- state/live/proc-ship.json: attempts 2, cause 'jav_config local only', since 18:40:37Z, while state/live/ship.log shows the deploy up ('Container osrs-openrune Started', 'live: a7fec6220...') and state/live/tree.json was written 1 min after the proc record. The next successful deploy raises the same alert for live (planner-32 was spawned on 'live: ship ended 3 times without a result since 2026-11-02T16:04:13Z').

Fix at the mechanism, replacing the rule 'a result is <name>.json newer than proc-<name>.json' and the scripts' own 'rm -f proc-<name>.json on success': the process's exit status is its result. F.spawn records the exit code when the script ends (e.g. the spawned command writes it into state/<slug>/<name>.rc, or a wrapper does); start() counts an attempt only for a dead script with a non-zero (or missing: killed, host fault) exit status, and a zero exit resets the count. Drop the rm -f proc-ship.json lines from tools/track.sh ship() and any other script that does it.

Acceptance: a test where a script exits 0 three times on different args with the same last line raises no alert; one that exits non-zero three times on the same cause raises it once; one killed (no exit status) counts as a failure. After landing, state/ship-harness and state/live carry no alert after their next successful ships.

Also (filed): A script record with no exit status counts no strike once exit status is the result
Sweep 70 P0-a: state/live/proc-ship.json holds attempts 2, cause 'jav_config local only' (since 18:40:37Z) written under the old rule; landing harness-script-end-is-result does not reset it because live's args[0] is the server's track.sh, not hd.py, so newer() never fires and the next successful deploy is refused. Records written before exit status existed (no exit field) must count nothing. ship-harness hit the bootstrap deadlock (attempts 3 on landed ships; the fix itself could not ship): the orchestrator moved state/ship-harness/proc-ship.json to evidence/monitor/sweep-70-ship-harness-proc-ship.json once. Evidence: evidence/monitor/sweep-70.md
