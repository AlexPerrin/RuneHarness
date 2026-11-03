---
slug: harness-live-build-rsprot-local
track: harness
title: Live build finds the locally published rsprot
kind: change
priority: P0
deps: []
created: '2026-11-01T11:54:36Z'
---
The live ship died twice without a result (alert). state/live/build-1f1cb450554ab84fa6984bd3ada6dd68e8e6a682.log (also 5071ccb2, 1f5ab1ca): Could not find net.rsprot:osrs-241-api / osrs-241-shared / osrs-241-android 1.0.0-ALPHA-20261001.99, searched file:/home/ubuntu/.m2 and jitpack/openrs2/OpenRune hosting; required by :server:app > :api:net. The integration tree pins an rsprot version that exists only where it was published locally, so the live build cannot resolve it. Make the live build resolve the same rsprot the gate built with (or the integration refuse a version only local maven has), and report the failure as one alert, not one per tick.
