---
slug: h-ref-pins-audit
track: harness
priority: P0
deps:
- harness-local-auth-pin-out
- h-ref-server-bundle
---
# Audit every hd.yaml fork pin against the reference deployment

The user's word in h-reference-deployment: every pin in hd.yaml repos.fork.pins a reference deployment makes unneeded goes (local/local-auth first), each kept one gets its reason in the hd.yaml comment or docs/ARCHITECTURE.md. Check each of local/quest-test-fixture, local/android, local/local-auth, local/test-commands, local/world-settings, local/skip-cs2-packs, local/op-overrides, local/spotless-241 against the upstream bundle build (h-ref-server-bundle). Done when staging rebuilt with the reduced list deploys and a desktop reaches LOGGED_IN. Upstream blob shas: evidence/h-reference-deployment/upstream-shas.md (re-check before acting). Part of h-reference-deployment (PRD H8).
