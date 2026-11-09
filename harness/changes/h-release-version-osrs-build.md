---
slug: h-release-version-osrs-build
track: harness
priority: P2
---
# client releases are versioned <OSRS build>-v<our version>

The user (2026-11-09): a client release is named by the official OSRS Android build it repacks, then our version: OSRS build is the major revision, our version (0.1, 0.1.1, 1.0.1) the minor revisions, our patches. Slug example: osrs-runelite-242.3-v1.0.

Today: tracks/client/track.md says 'Releases are vX.Y.Z; autonomous builds are 0.1.x; a major version needs the user'; tracks/client/release-dev.sh tags v<VERSION>-dev.<N> and requires VERSION to be X.Y.Z; osrs-plugins-reverse VERSION reads 0.1.0 though v0.1.2 shipped (2026-10-25); the release notes name the game build only in prose ('build 241.4').

Done when: the release tag, GitHub release title and APK asset name carry both parts (e.g. tag 242.3-v1.0, title 'osrs-runelite 242.3-v1.0', asset osrs-runelite-242.3-v1.0.apk; dev builds 242.3-v1.0-dev.N); the OSRS build is read from the repacked base.apk's versionName (242.3), never typed; VERSION holds our next version only; track.md states the scheme and which bumps are autonomous (our patch) and which need the user (the release card, as today); the release notes name the server revision the build talks to (a 242.3 build needs a revision-242 server). The first release under it is the 242 client (fork-android-rsprot-242, the official 242.3 APKs in ~/osrs-plugins-reverse/242/).
