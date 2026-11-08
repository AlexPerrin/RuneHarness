---
slug: central-token-login-op
track: central
priority: P0
deps:
- central-rights-test-mod
- harness-central-build-gradlew
---
# Central: token LOGIN op on the world link (openruneCentral 2.0.3), in the v9 ledger

server-token-auth (e40d5e9, live) bumps the fork's openruneCentral to 2.0.3, which only Central's dev/central-token-login-op (0485930 feat: token LOGIN op on the world link, on remote fork) provides; it is unpublished and absent from the v9 ledger. server-android-token-login is built on dev/server-token-auth (the verifier it fixes exists nowhere else), so its candidate needs that Central head as a composite (deps), else gradle fails: Could not find dev.or2:openrune-central:2.0.3 (state/server-android-token-login/build-e5399e3be249b7709d38c1e8b4811b3a2c15b0ab-1.log). Adopt the existing dev ref as this change's head (no new code), then server-android-token-login takes it in deps.
