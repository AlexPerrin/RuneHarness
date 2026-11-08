---
slug: client-host-initial-gamestate
track: client
priority: P1
---
# The host drops every GameStateChanged before its bus is ready: a start that reaches gameState 1000 before 'host ready' logs no state at all

Run 191 (QA of h-mobile-login-page-9, start 8, 23:37 UTC 2026-11-07, APK tree fef4307 = a32dd70): the app sat on its start error page 'Error connecting to server' (overlay gameState 1000, evidence/h-mobile-login-page-9/qa-start8-stuck.png) and the host logged no GameStateChanged line at all (qa-start8-stuck.logcat.txt: jav_config.ws served 18:38:33.105 local, 'host ready' 18:38:33.536, nothing after). native client_thread.cpp after_cycle posts GameStateChanged only on a change, from the first hooked cycle (23.7 s), and Host.onEvent returns while eventBus is null, so every change before 'host ready' is lost; a state reached before it and never left (1000) is never posted, and mobile_login.py (which reads the host's GameStateChanged/raw lines, e436464) cannot tell that page from a start and waits forever. Desktop RuneLite's plugins see every change from the client's start. Done when the host, once ready, posts GameStateChanged for the game's current state (raw included, the line's prefix kept: 'GameStateChanged <name> (raw <n>, ...'), so a start that ends on 1000 before 'host ready' logs 'GameStateChanged UNKNOWN (raw 1000' once, and a normal start still logs its states in order.
