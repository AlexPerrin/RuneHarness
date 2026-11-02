---
slug: server-js5-idle-relogin
track: server
title: a client whose JS5 connection the server idle-closed fails its next login's
  interfaces (no inventory, null NPC names)
kind: change
priority: P1
deps: []
created: '2026-11-02T07:46:55Z'
---
Cause observed in evidence/harness-relogin-inventory/cause.md (recordings and client logs in failing-login/, failing-login-2/): the server closes a JS5 channel after 30 s without traffic (rsprot DefaultIdleStateHandlerSupplier.JS5, read and write idle; OpenRune api/net NetworkFactory keeps rsprot's IdleStateHandlerSuppliers default). A client that logs in more than 30 s after its last cache request reconnects JS5 during the login and runs the login's interface onLoad scripts before the re-requested groups arrive: clientscript errors 547/458 (prayer_redraw IF_GETWIDTH) and 9447/2616/2262 (magic_spellbook_init IF_SETOPBASE) on component -1, the inventory widget (149) never gets its slots although the server sent update_inv_full 93 and if_opensub 161:79 149 (same packets as the good first login). Every failing second login in state/ (up, restart, keepers, RESUME up: server-world-entities, server-clan-guest, server-clan-channels, quest-cooksassistant, quest-sheepshearer, harness-relogin-inventory x2) has this JS5 reconnect; quick relogs within 30 s never fail. Fix in the server's network setup so a client's JS5 connection stays open while the client holds it (a JS5 idle supplier that does not close a logged-out client's channel), matching the official server as far as the client shows it (the official client keeps one JS5 connection for the session and does not expect it closed). Acceptance: on the fixed image, track.sh up 3 on a loaded host (other runs up) passes its second logins, then 5 restarts and 5 logout-and-login cycles of every desktop, each login made after the JS5 idle handler has fired on that desktop's channel (an observed fact: before the fix it closes the channel, after it keeps it), never a timed wait: 33 second logins, each LOGGED_IN with container 93 in the widget, no 'Client error: 547' in any desktop's client.log; before the fix the same sequence FAILs.
