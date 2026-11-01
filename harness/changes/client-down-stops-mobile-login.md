---
slug: client-down-stops-mobile-login
track: client
title: track.sh down stops mobile_login.py
kind: change
priority: P1
deps:
- harness-mobile-devtools-jar
- harness-down-stops-mobile-login
created: '2026-11-01T04:04:00Z'
---
From the harness-mobile-devtools-jar hand-back: mobile_login.py kept running after track.sh down stopped the emulator; down does not stop it (Processes rule: down stops what the run started). down stops the run's mobile_login.py with the emulator. Proof: after down, no mobile_login.py of that run is alive. One test per requirement touched.
