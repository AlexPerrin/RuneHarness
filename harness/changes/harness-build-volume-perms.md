---
slug: harness-build-volume-perms
track: harness
title: 'Every server build fails: the build volumes are root-owned'
kind: change
priority: P0
deps: []
created: '2026-10-31T23:50:49Z'
---
tools/track.sh build fails for every server slug. The docker volumes gradle-<slug>, or-dl and or-cache-store are owned by root:root with mode 755, and the build runs as uid 1000, so mkdir -p $HOME fails with Permission denied. Log: state/cannon-review-354/build-9339b8822a071e3ab91a07e3d7ae1f0131096b40.log (cannon-review-354-2, head 7a8b2331a). The track script must create the volumes owned by the build's uid, or run the build as their owner. The script is on the fork's local/harness branch. One test per requirement touched.
