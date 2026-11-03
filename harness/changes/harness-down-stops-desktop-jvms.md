---
slug: harness-down-stops-desktop-jvms
track: harness
title: track.sh down stops its desktop JVMs and removes their instance
kind: change
priority: P1
deps: []
created: '2026-11-01T06:39:55Z'
---
quest-restlessghost-8 hand-back: 'track.sh down quest-restlessghost' removed run/4/owner but left all three run4 desktop JVMs running (marked osrs-test-run4 for that change), and rm of /mnt/c/osrs-test/run/4 failed with Permission denied because the JVMs held the files. The dev stopped them by hand with taskkill and removed the dir. down came from harness-desktop-instances-per-run (kill by marker, wait until gone, then delete). Expected: down stops every JVM whose marker is one of its slug's instances, waits until none is alive, then removes the instance dirs; it removes the owner file last, so a failed down can be re-run. Also seen: the dev's 'track.sh build' was refused because a container build-<slug> was already running (the loop's own build of the same change); a dev's build waits for or reuses that build instead of failing. One test per requirement touched.
