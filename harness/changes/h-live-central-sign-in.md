---
slug: h-live-central-sign-in
track: harness
priority: P1
deps:
- central-game-session
---
# The live stack serves Central's sign-in to desktops over https

Once central-game-session is on staging: tracks/fork/track.sh deploy runs the live game with embedded Central's sign-in on, as tracks/fork/track.sh up does with SIGN_IN=central (track.sh 217-222): OPENRUNE_SIGN_IN_TOKEN_SECRET the live issuer's secret (state/live/token, the one game.yml's token-login block holds), OPENRUNE_SIGN_IN_DEV_ACCOUNT the APK's tester (state/live/token/account), OPENRUNE_HTTP_TLS_PORT with a PKCS12 of the live tls.pem/tls.key, and Central's http and https ports published in docker-compose.yml. Today the live stack has no sign-in a desktop can use: issuer.py's https listener (container 8080) is unpublished, compose maps only its http 8081 for the APK, and osrs-openrune-http-desktop's jav_config names its own http base in params 11 and 22, which the desktop casts to https. Done when javcheck.py passes on the live Central's /jav_config.ws and a curl of its https /.well-known/openid-configuration with the live tls.pem answers 200, the APK's sign-in unchanged. Unblocks h-desktops-token-login (option b of question 11: live-desktop signs in through Central).
