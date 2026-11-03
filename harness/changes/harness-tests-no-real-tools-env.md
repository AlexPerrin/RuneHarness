---
slug: harness-tests-no-real-tools-env
track: harness
title: the suite's ship tests never see the gate's TOOLS; no test moves or pushes
  a real tools branch
kind: change
priority: P0
deps: []
created: '2026-11-01T05:54:02Z'
---
tools/track.sh gate runs check-tests with the change's TOOLS in the environment (hd.py:499 sets TOOLS for track.sh). tests/test_hd.py R8.test_ship_fast_forwards_the_live_branch_or_regates runs track.sh ship with env={**os.environ, ...}, so it inherits the real TOOLS and ship acts on the real carried tools branches. Evidence: harness-up-own-keys gate on fd86343da (05:45:14Z) and on cbfa4b7a5 (05:51:41Z) both failed 'FAIL: test_ship_fast_forwards_the_live_branch_or_regates (test_hd.R8...)' together with 'check-tools: /home/alex/src/OpenRune-Server: abc4426ab... is not a fast-forward of local/harness'; harness-desktop-instances-per-run (no carried tools) passed the same suite at cbfa4b7a5 (05:52:21Z). When the carried head does fast-forward, the same test would fast-forward the real fork's local/harness and push it to 'fork' before the gate passes. Expected: every test that runs track.sh builds its env without the gate's TOOLS (and any other loop env it does not set itself), so the suite's result and side effects are the same with or without a carried tools head. Proof: the R8 suite passes with TOOLS set to a non-fast-forward real-looking value and leaves that repo's branch and remote untouched. One test per requirement touched.
