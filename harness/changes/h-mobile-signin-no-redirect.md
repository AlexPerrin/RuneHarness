---
slug: h-mobile-signin-no-redirect
track: harness
priority: P1
deps:
- h-mobile-boot-monkey-aborted
---
# mobile_login: after Sign in at Central's form Chrome stays on the filled form with no redirect to the app, and up waits on it with no end

Run 310, live stack, h-mobile-loading-stall's worktree (f57a2a3: mobile-allow relays non-TLS 443 to 43594), emulator-5562, account hb0692198bm. Ten-start loop: starts 1-5 LOGGED_IN (02:24-02:59 UTC); start 6 tapped Sign in (input tap 94 476 = the button [21,446][168,506]) at 03:05:49 UTC and then sat 40 min on Chrome's custom tab at 10.0.2.2:8084, title 'Sign in', both fields still holding the name, LoginIndex 30, until down. No RedirectUriReceiverActivity START (each successful start's logcat has one within seconds of Sign in); instead Chrome showed a message bar 18 s after the tap (cr_MessagesMetrics 'Triggered message stacking animation type 1' 03:06:07, removed 'reason 3' 03:06:18), which no successful start's logcat has: likely Chrome's prompt before opening the app for the redirect to com.jagex.mobilesdk.android.osrs:/oauth2redirect (not confirmed: its text was gone before the next read). No HTTP access log on Central (osrs-openrune 9090) or the issuer shows whether the post arrived. mobile_login.form() treats a posted form whose fields are not empty as 'the posted page stays drawn until the redirect' and waits with no end. Evidence: evidence/h-mobile-loading-stall/s6.logcat.txt, s6.ui.xml, s6.sockets.txt, s6-focus.txt, ten-starts-2.txt. Find what the message is and why the redirect did not happen (read it in the dump while shown, or Chrome's external-navigation rule), act on it or fail on the observed fact; never a wait with no end. Done when tracks/client/track.sh up <slug> prints LOGGED_IN on 10 consecutive starts (with h-mobile-loading-stall's allow.py).
