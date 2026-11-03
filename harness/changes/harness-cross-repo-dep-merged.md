---
slug: harness-cross-repo-dep-merged
track: harness
title: A card waits while an upstream dependency in another repo is not merged
kind: change
priority: P1
deps: []
created: '2026-11-01T21:17:41Z'
---
Found by the read-only monitor sweep (2026-11-01 ~21:12Z) the user asked for. deps_held (hd.py:792) checks the upstream merge only for same-track deps; Central counts as live once gated (live(), hd.py:504). So server-token-auth's card can come while the Central PR it 'Depends on' is not open (the user holds central-token-login-op). Acceptance: public() holds a card while any dependency that goes upstream in another repo is not merged there ('waiting on X's upstream merge'); the test-server deploy is unchanged; a test covers it.
