---
slug: h-mobile-launch-unresolved
track: harness
priority: P2
---
# client up (3f9853a, am start -W -c LAUNCHER -p pkg) fails 3 times in a row on a fresh Agent_Phone: unable to resolve Intent for the app package



## alert 71 fault 322 (×2, first 2026-11-09T05:26:00+00:00)
root cause of the up failure above: am start resolves with MATCH_DEFAULT_ONLY and the app's MAIN/LAUNCHER filter has no category.DEFAULT (cmd package query-activities finds MainActivity with isDefault=false), so 'am start -W -a MAIN -c LAUNCHER -p com.jagex.oldscape.android' can never resolve; tracks/client/track.sh up should start it as -n com.jagex.oldscape.android/com.jagex.android.MainActivity. Every client up fails since 3f9853a.
