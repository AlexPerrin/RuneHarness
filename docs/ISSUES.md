# Issues

- **Feature proposals for the held cards' changes are not yet asked.** Once h-feature-prs ships, each proposed bundle
  is one `hd ask` on its first change with an option `feature <branch> <slug…>` for the user: session reliability
  (server-reconnect, server-resumed-session-logout, live-session-drops-after-login); Central auth with its server
  sister (central-token-login-op, central-embedded-jav-config, central-game-session, central-sign-in-first-account,
  server-token-auth); friends (fork-presence-push-not-delivered, fork-private-filter-reverts-at-login,
  fork-friend-add-updates-list, central-friend-del-no-offline-push); world switcher (server-world-switcher). The open
  PRs #408, #354, #367, #450 already carry their features (feat/hunter, content/cannon, content/goblin-diplomacy,
  content/server-training-bow); fork-staging-merges-main-242 keeps a dead `upstream:` key (edited in the live checkout).
- **An absent ledger is created silently.** `store` opens `state/hd.db` and runs the migrations on an empty file, so an
  orchestrator started in a checkout without the ledger planned every change from nothing: 5 dev runs of changes long
  landed, a staging deploy. Root cause: a missing ledger is indistinguishable from a first start. Fix: create the ledger
  only by an explicit command (`hd init`); every other command refuses a missing `state/hd.db`.
