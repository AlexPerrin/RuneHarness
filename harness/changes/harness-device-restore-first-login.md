---
slug: harness-device-restore-first-login
track: harness
title: The client restore check fails after any first login
kind: change
priority: P1
deps: []
created: '2026-11-01T01:10:05Z'
---
Client down reports RESTORE FAILED: the app writes settings.properties and new files after the backup, and settings.properties does not exist at backup time on a fresh install. The backup must be taken from the state the restore should return to, or the check must compare against the install-time baseline the harness owns. Evidence: evidence/harness-no-powershell/proof.md (harness-no-powershell-2). One test per requirement touched.
