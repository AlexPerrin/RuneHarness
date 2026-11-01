---
slug: harness-hook-approve-in-pattern
track: harness
title: The PreToolUse rule denies a read-only command that only mentions hd.py approve
kind: change
priority: P1
deps: []
created: '2026-11-01T12:45:46Z'
---
Hand-back of harness-deprecate-head-1: the live hook denied a read-only grep because its text had 'hd.py approve' right after a '|' inside the grep pattern. The rule matches command text, not the program run. Acceptance: a command that runs hd.py approve or close is denied; a command that only contains that text as an argument (grep, cat of a file naming it) is allowed; a test covers both.
