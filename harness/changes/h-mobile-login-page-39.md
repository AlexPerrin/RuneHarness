---
slug: h-mobile-login-page-39
track: harness
priority: P1
---
# mobile_login: LoginIndex 39 ends a start intermittently though the issuer answered 200

Page 39 is the client's error page, set by 0x47e824 (Ghidra 0x57e824) from the login handler 0x41615c, default text 'Connection failed during login request' (decomp 0057e824.c, 0051615c.c). It is a failure page, so do not add it to WAIT. On the live stack after local-cs2-group-names: 1 start of 6 ended 10 > 30 > 39 (evidence/local-cs2-group-names/page39-start.txt, 08:05:09 UTC), the others 10 > 37 > 30 > LOGGING_IN. The issuer log for the failed start is the same as a good one: every request 200, POST /game-session/v1/tokens logged about 0.5s after page 39, as in the good start. The game server saw no login. The page's message was not captured. Find the failing request and its status (the handler's status codes include -5, 1403, 1499): screenshot the page and capture the host's traffic on a failing start. Fix the cause, or if it is a client-side transient take the page's own Try again path once, in mobile_login step(). Done when tracks/client/track.sh up <slug> prints LOGGED_IN on 10 consecutive starts.
