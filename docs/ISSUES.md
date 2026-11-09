# Issues

- **An absent ledger is created silently.** `store` opens `state/hd.db` and runs the migrations on an empty file, so an
  orchestrator started in a checkout without the ledger planned every change from nothing: 5 dev runs of changes long
  landed, a staging deploy. Root cause: a missing ledger is indistinguishable from a first start. Fix: create the ledger
  only by an explicit command (`hd init`); every other command refuses a missing `state/hd.db`.
