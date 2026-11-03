---
slug: harness-emulator-lock-held
track: harness
title: A running emulator holds the client track's port lock
kind: change
priority: P0
deps: []
created: '2026-11-01T02:10:02Z'
---
In the client track's tools/track.sh boot(), the emulator starts as (cd /mnt/c && setsid emulator.exe ... 9>&- &): the 9>&- closes the lock fd for emulator.exe only, and the background-list bash that forks it (alive for the emulator's whole life) keeps fd 9, so state/emulator-port.lock stays held until that emulator exits. Seen 2026-10-31 21:55 ET: pid 1005902 (client-api measure's emulator parent, stuck in device_login) held the lock and up/measure of client-launch, client-launch-measure and harness-device-egress-ip waited on flock. Fix: close fd 9 for the whole subshell, (cd /mnt/c && setsid ... &) 9>&-. Test: a fake emulator that sleeps; after up returns, flock -n on the lock succeeds (fails on the old line). Both are in evidence/harness-device-egress-ip/wip-tools.patch (test_a_running_emulator_holds_no_lock). One test per requirement touched.
