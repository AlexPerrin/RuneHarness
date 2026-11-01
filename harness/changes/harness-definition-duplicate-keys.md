---
slug: harness-definition-duplicate-keys
track: harness
title: a definition with a repeated frontmatter key is refused, not read last-wins;
  the 15 doubled deps merged
kind: change
priority: P0
deps: []
created: '2026-11-01T01:14:14Z'
---
Commit 475b18e (client changes wait on harness-device-network-block) prepended a second 'deps:' line to definitions that already had a block 'deps:'. hd.py:170 _frontmatter reads them with yaml.safe_load, which keeps the last key silently, so the added dep is dropped.

Evidence:
- harness/changes/client-launch-measure.md has 'deps: [harness-device-network-block]' at line 3 and 'deps:\n- harness-no-powershell' at line 8; hd shows 'change: client-launch-measure [client P1]: dev run due' (events.jsonl 2026-11-01T01:10:49Z) while every other client change is 'waiting on harness-device-network-block'. Its dev run would start an emulator before Jagex hosts are blocked (privacy rule).
- Same doubled key, intended dep ignored: client-devtools-login, client-launch-boot, client-launch-dialogs, client-launch-files-init, client-launch-host-start, client-launch-install (network-block dropped); cannon-354-reset-ammo-varp, cannon-354-reset-mcannonmulti, cannon-354-return-after-destroy, genie-355-bank-lamp, server-clan-broadcasts, server-clan-channels, server-clan-guest, server-clan-hall (harness-no-powershell dropped, done, so harmless now).

Fix: _frontmatter refuses a definition with a repeated top-level key (the pass reports it as the change's state, it is never listed for a run), and the 15 definitions carry one merged deps list each. One test: a definition with two deps keys is refused.
