---
slug: h-live-apk-central-sign-in
track: harness
priority: P0
deps:
- h-live-central-sign-in-deployed
---
# The live deploy's APK jav_config names Central's http sign-in instead of osrs-openrune-issuer

Run 239 (client-android-central-sign-in) found the APK cannot reach Central's sign-in on the live stack from the client clone: the APK reads jav_config from osrs-openrune-http (10.0.2.2:8080), whose params 11, 20, 22 and 28 tracks/fork/track.sh deploy (line 306) writes as http://{{WORLD_HOST}}:${OPENRUNE_ISSUER_PORT:-8083}/, the issuer.py container; curl http://127.0.0.1:8080/jav_config.ws on the live stack (tree ae9574c8) shows param=11/20/22/28=http://10.0.2.2:8083/. Needed, once h-live-central-sign-in-deployed publishes Central's http 8084:8080 with OPENRUNE_SIGN_IN_TOKEN_SECRET (the issuer's secret) and OPENRUNE_SIGN_IN_DEV_ACCOUNT (state/live/token/account, tester): the deploy's APK template names Central's plain-http port (http://{{WORLD_HOST}}:8084/; Central's SignInRoutes publicBase() takes the request's Host, so discovery answers http://10.0.2.2:8084/ to the APK; the APK takes http under LOCAL_AUTH, not the live self-signed https), and the deploy checks Central's http /.well-known/openid-configuration answers 200. The issuer container may stay until h-ref-sign-in-no-issuer removes it. Done when the live 8080 jav_config names 8084 in params 11, 20, 22, 28 and tracks/client/track.sh up client-android-central-sign-in reaches LOGGED_IN on the live stack.
