---
slug: harness-staff-rights-intermittent
track: harness
title: STAFF rights hold on every up, not on a retry
kind: change
priority: P0
deps: []
created: '2026-11-01T07:43:08Z'
---
quest-restlessghost-9: the first 'STAFF=1 tools/track.sh up quest-restlessghost 1' ended with 'up: the accounts' rights did not hold after the login' (the read-back added by harness-server-up-staff-rights) and the account's rights read back empty; a down and the same up again worked. quest-runemysteries-6 saw the same empty rights before that read-back existed; harness-server-up-staff-rights-1 could not reproduce it and found no writer of accounts.rights after creation. So something still empties or never sets rights on some ups. Expected: find the observable cause (ordering against the account's creation on first login, a second account row, the update matching zero rows) and make the update land on every up; the read-back stays as the check. Proof: ten consecutive STAFF=1 ups all hold rights. One test per requirement touched.
