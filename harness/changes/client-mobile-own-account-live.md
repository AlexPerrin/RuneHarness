---
slug: client-mobile-own-account-live
track: client
priority: P1
deps:
- h-allow-relay-dns-again
- h-mobile-form-fields-filled
- h-mobile-loading-stall
- h-mobile-login-page-9
---
# Parallel mobiles on the live stack each sign in at Central's form as their slug's own account

Checked once h-mobile-login-page-9 is live and its deploy recipe fork-2 has redeployed the live stack (osrs-openrune without OPENRUNE_SIGN_IN_DEV_ACCOUNT; at qa run 282 the live container still set it to tester, so the form path was never exercised). With two mobiles up at once (two slugs, tracks/client/track.sh up each), both print LOGGED_IN, each up's stderr shows "Central's sign-in: h<sha>m" with its own name, the server log shows two distinct users logged in and no 'Login refused ... response=Duplicate'; then a start of one slug prints LOGGED_IN while another slug's mobile stays logged in.
