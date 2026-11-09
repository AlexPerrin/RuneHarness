---
slug: h-spawn-waits-on-dep
track: harness
priority: P2
---
# decide spawns a dev for a change whose dep is not landed; its probe criterion cannot pass



## alert 55 fault 185 (×1, first 2026-11-07T20:44:19+00:00)
run 185 (dev client-host-raw-gamestate) was spawned while its dep live-session-drops-after-login is not landed (that change itself waits on server-reconnect); the probe criterion cannot pass: measure at e436464 at 15:38-15:43 EST again ended mobile LoginIndex 9 and desktop 'client is gone', the failure that dep records. The code (e436464) is already on origin/client/client-host-raw-gamestate and its raw line is shown in evidence/client-host-raw-gamestate/logcat-host*.txt
