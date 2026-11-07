---
slug: server-reconnect
track: fork
priority: P1
---
# server: a reconnect after a lost connection is refused ConnectFail, the Android app ends on LoginIndex 9

On the live stack a first login of a fresh APK install (track.sh up: the app downloads the whole cache over js5, ~0.5 MB/s) sits in LOADING ~50 s (Oct starts: 1-20 s), the game connection is lost as LOADING ends (LOGGED_IN then CONNECTION_LOST in the same ms), the client reconnects, and the server answers ConnectFail: ConnectionHandler.onReconnect is a TODO that writes LoginResponse.ConnectFail. The app shows LoginIndex 9 'Unexpected server response / Please try using a different world.' Evidence: evidence/h-mobile-login-page-9/page9-timeline.txt, server-sockets-3.txt; evidence/h-mobile-login-page-39/1794040064-logcat.txt and -screen.png. Expected (official): a reconnect within the logout window resumes the session (rsprot ReconnectBlock with the session's XTEA keys) and the player stays logged in. Also find who closes the game connection during the long LOADING (rsprot's game idle handler is 15 s: DefaultIdleStateHandlerSupplier$Game) and whether the official server keeps a loading client; log every login refusal and every game-session disconnect with its reason (the server logs none today). Done when tracks/client/track.sh up h-mobile-login-page-9 prints LOGGED_IN on 10 consecutive starts on a stack carrying the change.
