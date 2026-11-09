---
slug: local-android-rsprot-token-gjstr
track: fork
priority: P1
upstream: false
---
# local/android: RSProt decodes the Android token (auth type 7) as a jstr, without its 0x00 terminator

The fork's patched RSProt (local/server-tools sidecar/rsprot.patch, published to the clone's .m2-rsprot as 1.0.0-ALPHA-20261001.99 and pinned by local/android) decodes auth type 7 (MOBILE_TOKEN_AUTHENTICATION, GameLoginDecoder.kt in osrs-241-shared) as the rest of the RSA block: 'val rest = ByteArray(buffer.readableBytes())'. The official Android client writes type 7 exactly like desktop type 2: the token as a jstr ending in one 0x00, the last byte of the plaintext (static RE of osclient.so 241.4, evidence/server-android-token-login/android-login-block.md: credential writer 0x4feb74, mask 0x184 arm for types 2,7,8). So the server receives <account>.<expiry>.<mac> plus a trailing NUL and TokenLoginVerifier (server-token-auth) refuses it: InvalidUsernameOrPassword on the live stack. Fix in the patch: MOBILE_TOKEN_AUTHENTICATION -> AuthenticationType.TokenAuthentication(Token(buffer.gjstr().toByteArray()), otp), the type-2 arm's decode; drop the 'not reverse engineered' comment; republish .m2-rsprot so local/android's build and staging carry it. Fork-only (upstream RSProt and upstream OpenRune accept no Android client; qa run 67 failed one-change/claims on the verifier-side workaround). Check: the official app's token login reaches the game on the stack (acc-1 wants a capture of the app's bytes: a server-side decode log of the type-7 credential bytes, hex, length), desktop 'up token' login unchanged. Once this lands, server-android-token-login drops its verifier NUL-trim commit 453a45ee3 (it compensates this decode) and needs no upstream PR.
