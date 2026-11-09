---
slug: h-live-central-sign-in-deployed
track: harness
priority: P0
deps:
- central-game-session
---
# The live stack serves Central's sign-in to desktops once central-game-session runs live

h-live-central-sign-in (08290b6) and h-desktops-token-login's live-desktop (52641cb) shipped while central-game-session was only submitted: every deploy failed its Central checks (javcheck on 8084 found Central's old jav_config, https 8443 answered 000) and live-desktop failed at sign_in. h-live-sign-in-needs-central reverted the live wiring; deps_live now holds this change until central-game-session is live. Reapply: deploy bakes the issuer's secret, account, a PKCS12 of tls.pem/tls.key and central_jav (sic=1, http 8443) into the live image with OPENRUNE_SIGN_IN_TOKEN_SECRET, OPENRUNE_SIGN_IN_DEV_ACCOUNT, OPENRUNE_HTTP_TLS_PORT=8443, the keystore and OPENRUNE_JAV_CONFIG_URL_TEMPLATE; compose publishes Central's 8084:8080 and 8443:8443; deploy checks javcheck on Central's /jav_config.ws and the https OIDC discovery with the live tls.pem; live_desktop signs the slug's own account in (sign_in "$(account 1)", tok=true sic=1, ca=state/live/token/tls.pem, http 8443) and logs in by token (desktop_login.py "$dt" token). See git show 08290b6 52641cb. Done when a deploy with central-game-session live passes those checks and live-desktop reaches LOGGED_IN.
