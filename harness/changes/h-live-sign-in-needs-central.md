---
slug: h-live-sign-in-needs-central
track: harness
priority: P2
---
# h-live-central-sign-in is done while the live Central lacks the https listener (central-game-session not on staging): TLS 8443 answers 000 and live-desktop fails at sign_in for every run



## alert 60 fault 215 (×1, first 2026-11-08T01:40:28+00:00)
h-live-central-sign-in is done, but the live stack deployed at 01:35Z (tree 3b74775d_cc6e461efc74e) answers no TLS on 8443: curl https://127.0.0.1:8443/.well-known/openid-configuration gets 000 and the container log shows only Central http 8080; its Central lacks the https listener (central-game-session not on staging), so tracks/fork/track.sh live-desktop fails at sign_in (curl 35) for every run
