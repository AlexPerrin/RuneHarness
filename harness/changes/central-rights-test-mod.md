---
slug: central-rights-test-mod
track: central
priority: P1
upstream: false
---
# Central: RightsTest compiles against Rights.MOD (upstream main's tests fail to compile)

Upstream main (d694191) renamed Rights.MODERATOR to Rights.MOD in central-common/src/main/kotlin/dev/or2/central/account/Rights.kt (55246f0 "2.0") but central-common/src/test/kotlin/dev/or2/central/account/RightsTest.kt still uses Rights.MODERATOR (b920862), so ':central-common:compileTestKotlin' fails (9 x Unresolved reference 'MODERATOR') and 'tracks/central/track.sh test' fails for every Central head off main. Repro: tracks/central/track.sh test central-token-login-op. Fix: RightsTest uses Rights.MOD (fix: subject, one upstream PR off main). Blocks central-token-login-op's tests criterion.

Fork-only: upstream's open PR #5 (Eikenb00m, "User rights fix") carries the same test fix; ours is dropped when it merges. The Central upstream hold stands.
