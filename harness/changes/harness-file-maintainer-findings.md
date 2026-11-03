---
slug: harness-file-maintainer-findings
track: harness
title: New maintainer inline comments on a PR are not filed as changes
kind: change
priority: P0
deps: []
created: '2026-10-31T23:42:50Z'
---
ARCHITECTURE says each maintainer finding files its own change on the PR with deps [the change]. On 2026-10-31 a-thoren left three inline comments on #354 (20:52-20:55Z) and one on #355 (20:47Z); the pass filed none. The qa contract runs for cannon-review-354 and genie-review-355 found them by hand, and the head filed cannon-354-reset-ammo-varp, cannon-354-reset-mcannonmulti, cannon-354-return-after-destroy and genie-355-bank-lamp. Make the loop file them from the PR's review comments. One test per requirement touched.
