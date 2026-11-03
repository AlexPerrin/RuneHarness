---
slug: harness-merge-resolution-follows-head
track: harness
title: a pin merge resolution is lost when the change's head moves
kind: change
priority: P1
mechanism: tree
deps: []
created: '2026-11-02T02:22:32Z'
---
server-token-auth-15 hand-back: the integration-tree conflict in ConnectionHandler.kt between server-token-auth and the pin local/local-auth (a8cae09) already had a resolution, fork/local/merge/113f93a-a8cae09, recorded under the older head 113f93a; hd looks resolutions up by the current head's 7-char sha, so a comment-only head move (e40d5e9) dropped it and cost a dev run to re-push it as local/merge/e40d5e9-a8cae09 (a4f6a8078; git rerere replayed it). A recorded resolution carries to the change's next head when it still applies (e.g. rerere at merge time), so only a resolution that no longer applies sends the change to dev.
