---
slug: harness-desktop-orphan-clients
track: harness
title: A desktop instance with a live orphan client is treated as free
kind: change
priority: P1
deps: []
created: '2026-11-01T02:44:28Z'
---
server-world-entities-4: desktop4 had no pid file, but an orphan client of server-friends-chat-clan-channels (account h4dad2b6391) was still running on it after that run's server and up.json were gone. desktop_start launched a new client on top of it, and the judge typed login keys into the orphan before noticing. A desktop5 client of that judge may also be left running without a pid file. Claim a desktop instance only when no client answers on its devtools port, whatever the pid file says. Have down stop each client by its devtools port and Windows PID, recorded at start. Add a sweep in up that stops any client on a claimed instance's port that no live run's up.json owns. Do not touch any Java process that is not a harness desktop client on a harness devtools port: the user's own RuneLite must never be touched. One test per requirement touched.
