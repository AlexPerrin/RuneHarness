---
slug: harness-desktop-devtools-jar
track: harness
title: Desktops load the devtools jar from the client build
kind: change
priority: P0
deps:
- harness-mobile-devtools-jar
created: '2026-11-01T04:04:00Z'
---
From the harness-mobile-devtools-jar hand-back: desktops take no jar from the client build, so the devtools login tool reaches only the mobile. The desktop clients started by the server track's up load the devtools plugin built by the client track (the same build the mobile gets), so harness-desktop-login-devtools can call the login tool. Proof: a desktop started by up answers get_client_state from the client build's devtools. One test per requirement touched.
