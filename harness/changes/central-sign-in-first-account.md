---
slug: central-sign-in-first-account
track: central
priority: P1
deps:
- central-game-session
---
# Central's sign-in signs in an account that has never logged in, as the game's first login makes it

central-game-session's POST /oauth2/auth (dev/central-game-session 148956e, SignInRoutes.kt:62, SignInService.checkPassword) signs in only the configured dev account or an account AccountRepository already holds whose password verifies; an unknown username returns null. The game's own first login registers the account (SessionService.kt:87-95: insertIfAbsent with the password's hash, the token login with an empty one). So a desktop whose account has never played cannot sign in through Central: tracks/fork/track.sh live-desktop logs in as the slug's own account (account 1 of the slug, password = name, never the tester), made today by its first typed login, and the live stack's dev account is the APK's tester. Needed: a password sign-in naming an account that does not exist registers it the way SessionService's first login does (same name policy, collision key and hash), then signs it in; an existing account still needs its password. Proved in-process: a fresh name signs in, its session's token logs the desktop in with only Play, and a second sign-in with a wrong password is refused. Unblocks h-desktops-token-login (option b of question 11: live-desktop signs in through Central).
