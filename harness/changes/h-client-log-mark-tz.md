---
slug: h-client-log-mark-tz
track: harness
priority: P2
---
# client track log: log-mark is UTC but logcat -T reads emulator local time



## alert 52 fault 163 (×1, first 2026-11-07T18:20:11+00:00)
tracks/client/track.sh: up writes state/<slug>/log-mark with date -u (UTC, 18:00:40) but log passes it to logcat -T, which reads it as the emulator's local time (13:00 EST), so 'track.sh log <slug>' returns nothing for 5 h after up
