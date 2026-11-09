---
slug: h-allow-relay-dns-again
track: harness
priority: P1
---
# mobile-allow: a transient upstream DNS failure (EAI_AGAIN) fails check-blocked and the up

Run 289, 20:27 UTC 2026-11-08: a second mobile's tracks/client/track.sh up (slug h-mobile-login-page-9, started beside client-mobile-own-account-live's) failed check-blocked 'NOT REACHED (no TLS answer on 443): api.runelite.net static.runelite.net' and restored: mobile-allow's relay (tracks/client/allow.py line 67, socket.create_connection((name, 443))) raised socket.gaierror [Errno -3] Try again at 20:27:22 and 20:27:38 (evidence/client-mobile-own-account-live/mobile-allow-gaierror.txt, up-b-parallel.err.txt); a minute later the same lookup in the container answered 172.67.74.139. EAI_AGAIN is the resolver's 'not now', not an answer: the relay resolves again until it gets one (or a definite NXDOMAIN), so a mobile's up does not fail on Docker's resolver hiccup. Done when check-blocked passes through such a failure (a test of allow.py's relay with a resolver raising EAI_AGAIN once) and two parallel ups both pass check-blocked.
