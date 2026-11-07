---
slug: h-mobile-login-start-error
track: harness
priority: P1
deps:
- client-host-raw-gamestate
---
# mobile_login waits forever on the app's start error page (gameState 1000, 'Error connecting to server')

Run 154 (h-mobile-login-page-39), up at 08:33 UTC 2026-11-07: the app stopped at its start error page, 'Error connecting to server. Please check your network connection and try again' (overlay gameState 1000, evidence/h-mobile-login-page-39/stuck.png); the host logged GameStateChanged UNKNOWN once and nothing after, so mobile_login step() returned wait for 25 minutes until killed. The page must be read as a failure (or its cause fixed): the host logs no state for gameState 1000. Done when step() fails that page by an observed fact and up ends.
