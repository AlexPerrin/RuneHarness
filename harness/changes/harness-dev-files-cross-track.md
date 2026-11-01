---
slug: harness-dev-files-cross-track
track: harness
title: A dev files a fix outside its track with hd new instead of asking where it
  goes
kind: change
priority: P1
deps: []
created: '2026-11-01T01:28:17Z'
---
Devs ask the user where a fix that belongs to another track goes, which needs no user (the user's OK is only for OpenRune upstream and client releases). Evidence: events 1113 client-loading-fullscreen-rotate ask: 'That code lives on client/harness-v8 ..., the harness track, not on this change's dev ref. Proposal: file it as a harness change ... Yes, or another placement?' (still open, blocking the change); events 634 genie-review-355 ask: 'I filed harness-gate-ci-slug (uncommitted definition). Please commit it and make genie-review-355 depend on it'; events 240 harness-track-carries-tools-branches ask: 'Add deps: [harness-ship-onto-live-branch]'. Fix: .claude/agents/dev.md says a fix outside the change's track is filed with 'hd new --track <t> --deps ...' and the change gains it as a dep (an hd verb that adds a dep to the running change if none exists), then the run hands back; hd ask stays for decisions only the user can make. One test per requirement touched.
