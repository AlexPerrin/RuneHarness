---
slug: harness-desktop-instances-per-run
track: harness
title: Each up gets its own desktop instances; no shared pool of five
kind: change
priority: P1
deps: []
created: '2026-11-01T05:28:23Z'
---
server-friends-chat-clan-channels-9 hand-back (after harness-desktop-instance-race shipped): all five desktop instances are shared, so 'track.sh up <slug> 2' races other runs and needed a retry loop to get two at once. The standing rule is no device locking: every run its own client windows, in parallel, no cap. Expected: up creates the instances it needs (its own home, ports and window) instead of taking from a fixed pool, so an up never waits on or fails for another run's clients, and down removes exactly its own. Proof: three concurrent ups of 2 desktops each all log in on the first try. One test per requirement touched.
