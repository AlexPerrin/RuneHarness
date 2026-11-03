---
slug: harness-server-up-members-account
track: harness
title: 'track.sh up dies at the members update: account() called without an argument'
kind: change
priority: P1
deps: []
created: '2026-11-01T02:06:45Z'
---
OpenRune-Server tools/track.sh up (.worktrees/harness, b7f75e2ee): the members psql line calls $(account) with no argument; account() reads $1 under set -u, so up exits with 'line 33: $1: unbound variable' after the first login. The members update and the relog never run, and the client is left at the login screen (up printed LOGGED_IN, the error, then 'FAILED: back at the login screen'). Fix: match the accounts of this up (the h<hash> prefix without the index, e.g. a prefix variable or ${1:-}). Seen in run quest-cooksassistant-3, state/quest-cooksassistant. One test per requirement touched.
