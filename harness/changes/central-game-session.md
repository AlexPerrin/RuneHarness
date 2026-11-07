---
slug: central-game-session
track: central
priority: P1
deps:
- central-token-login-op
---
# Central serves the official client's sign-in: OIDC and game-session endpoints that mint the login token

Port tracks/fork/server/issuer.py into Central's Ktor routes (central-app/src/main/kotlin/dev/or2/central/http/CentralHttpRoutes.kt), so no sidecar issues tokens and no client types a password. Endpoints, same shapes as issuer.py and the official client's AppAuth: GET /.well-known/openid-configuration; GET /oauth2/auth (a code back to redirect_uri with state); POST /oauth2/token (access, refresh, id_token); GET /userinfo; GET /jwks; POST game-session/v1/sessions {idToken} -> {sessionId}; GET game-session/v1/accounts with Bearer sessionId -> [{accountId, displayName, userHash}]; POST game-session/v1/tokens -> {token}. The token is the compact <account>.<expiry>.<HMAC-SHA256> the game verifies (TokenLoginVerifier, at most 67 bytes: the client carries it in its RSA login block), its secret Central's config. The account comes from Central's accounts (AccountRepository), the password checked by PasswordHasher; a dev realm may sign in a configured account at once, as issuer.py does. Central already serves /jav_config.ws, /worldslist.ws and /worlds.js: extend its jav_config so params 11, 20, 22 and 28 name these endpoints, which also replaces the http sidecars. Prove it in-process: the game with central.same-instance reaches them, a fresh RuneLite desktop with the JX_ session variables logs in through them with no key typed but Play, and the Android login once deployed (the fix local-android-rsprot-token-gjstr is on staging). Fork first: the user's Central upstream hold stands until the login work clears.
