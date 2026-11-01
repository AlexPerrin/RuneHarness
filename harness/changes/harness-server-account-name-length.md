---
slug: harness-server-account-name-length
track: harness
title: Desktop login account names are too long
kind: change
priority: P1
deps: []
created: '2026-11-01T01:10:05Z'
---
Server up with a desktop client builds the account name from the slug (harness-no-powershell1, 22 characters), which is too long for an OSRS login name (12 characters max), so desktop_login fails. Derive a short unique name per run and record the mapping in state. Evidence: evidence/harness-no-powershell/proof.md (harness-no-powershell-2). One test per requirement touched.
