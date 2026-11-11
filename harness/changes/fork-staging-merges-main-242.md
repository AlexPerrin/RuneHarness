---
slug: fork-staging-merges-main-242
track: fork
priority: P2
upstream: false
deps:
- fork-android-rsprot-242
- h-fork-revision-242
---
# Upstream main fccf79f82 (rev 242) does not merge onto staging

Run 412 (2026-11-09): dev/fork-friend-add-updates-list 5f57044 merged with upstream main fccf79f82 (242 #471, 'wire missing 241-242 packets') stops tracks/fork/track.sh build at 'conflict: api/net/src/main/kotlin/org/rsmod/api/net/rsprot/RspCycle.kt api/player-output/src/main/kotlin/org/rsmod/api/player/output/Camera.kt gradle/libs.versions.toml'. Staging is behind upstream main (origin/main not an ancestor of fork/staging), so no change branched off current upstream main builds a candidate. Done when a head at current upstream main merges onto staging and track.sh build succeeds for it.

## the official Android 242 APKs are in place
The user's answer a (move to 242): the official OSRS Android 242.3 (versionCode 24203008, Google Play, pulled 2026-11-09 from the user's Pixel 9a) is at ~/osrs-plugins-reverse/242/base.apk (sha256 c0b6e906...376e) and ~/osrs-plugins-reverse/242/split_config.arm64_v8a.apk (sha256 c970da69...abcc8). The 241.4 pair stays at ~/osrs-plugins-reverse/base.apk and split_config.arm64_v8a.apk for the live client until the port lands.
