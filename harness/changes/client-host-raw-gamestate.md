---
slug: client-host-raw-gamestate
track: client
priority: P1
deps:
- live-session-drops-after-login
---
# The host's GameStateChanged line names the game's raw state (1000, the start error page, logs as UNKNOWN)

Host.java GAME_STATE_CHANGED maps the native state through GameState.of(a), so every value outside RuneLite's enum logs 'GameStateChanged UNKNOWN': the start's loading states and 1000, the app's 'Error connecting to server' page (evidence/h-mobile-login-page-39/stuck.png, overlay gameState 1000), alike. The devtools get_client_state gives client.getGameState().name(), UNKNOWN too, so nothing the harness reads tells that page from a start. Done when the host's GameStateChanged line carries the raw int (e.g. 'GameStateChanged UNKNOWN (raw 1000, getGameState UNKNOWN, ...)') on every change, the line's existing prefix kept (tracks/client/mobile_login.py reads 'GameStateChanged (\w+)'). h-mobile-login-start-error then fails raw 1000 in mobile_login step().
