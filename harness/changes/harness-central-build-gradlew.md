---
slug: harness-central-build-gradlew
track: harness
priority: P1
---
# tracks/central/track.sh build and test fail: ./gradlew not executable, no candidate without a key

Upstream Central commits gradlew as mode 100644 (git ls-files -s gradlew), so the gradle() helper's ./gradlew fails in the container: '/__cacert_entrypoint.sh: line 123: .../central-token-login-op-build/gradlew: Permission denied' (run 44, build of 0485930). Fix: run it as 'bash ./gradlew' (build, test, and the fork track's CENTRAL composite if it runs the Central wrapper). Same verb: 'track.sh build <slug>' with no key and no TCOMMIT runs 'git reset --hard ""' (fatal: ambiguous argument ''); a dev before its first candidate has no key: default the checkout to dev/<slug>. Test: track.sh build on a clone whose gradlew is 100644 assembles.
