---
slug: harness-device-boot-failure-cleanup
track: harness
title: A failed client boot leaves its emulator running and no serial
kind: change
priority: P1
deps: []
created: '2026-11-01T01:18:06Z'
---
In the client's tools/track.sh (client/harness-v8), up runs 'boot > $state/serial' and boot prints the serial only at its end, so a boot that fails (the install failure in state/client-api/measure.log) leaves an empty state/client-api/serial and an emulator nothing stops: adb devices lists emulator-5562 and emulator-5564 while only state/client-launch/serial names one (5564), and measure never runs down after a failed up. Write the serial as soon as the emulator is started and stop it on any failure in up or measure (down on every exit path). Also check the free-port pick for two concurrent boots (client-api and client-launch measures started 01:12:53Z and 01:14:16Z): the INSTALL_FAILED_DUPLICATE_PACKAGE 'pending install requests' suggests two installs reached one device. Carry the fix on client/harness-v8. One test per requirement touched.
