---
slug: server-android-token-login
track: fork
priority: P1
deps:
- central-token-login-op
- harness-composite-image-tag
---
# token login: the official Android app's token is refused (Incorrect password or username)

server-token-auth (e40d5e9, live) verifies <account>.<expiry>.<HMAC-SHA256> tokens from tracks/fork/server/issuer.py; it was judged on a RuneLite desktop that sends the issuer's token verbatim, never on Android (its accuracy.md: no Android recording; the game-session token's length and character set unsourced). On the live stack the app's sign-in completes (openid-configuration, oauth2/auth, oauth2/token, game-session sessions, accounts, tokens: all 200 from the issuer), then the game answers InvalidUsernameOrPassword: TokenLoginVerifier.accountName returned null. The issuer's secret and game.yml token-login.secret are the same key; container clocks match WSL. So what the Android login block carries is not the issuer's token as minted (a truncation, an encoding, or the OAuth id_token). Capture what the app sends under LOCAL_AUTH (the mobile reaches only the live stack: every APK carries the live modulus), then fix the server's verifier or the issuer's response shape so the official app logs in; the desktop token login (fork track 'up token') must keep working. Evidence: state/client-api/measure-*.log (LoginIndex 9 after Play Now), docs in evidence/server-token-auth/accuracy.md (v8 checkout).
