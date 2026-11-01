---
slug: harness-server-log-empty
track: harness
title: The server track's log prints nothing, even for the pattern '.'
kind: change
priority: P1
deps: []
created: '2026-11-01T12:44:28Z'
---
Hand-back of server-npc-examine-without-overlay-3 (head 513110187): the server log search for ERROR|WARN|Exception printed nothing, and the same log command printed nothing for the pattern '.', on a server it had just built and played on. A run that greps the log for errors therefore reads a clean result it cannot trust. Acceptance: the server track's log verb returns the running server's lines (a '.' search is non-empty while a server it started is up); a test covers it.
