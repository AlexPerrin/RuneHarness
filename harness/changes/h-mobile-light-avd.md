---
slug: h-mobile-light-avd
track: harness
priority: P1
---
# the agents' emulator: no Play Store image at 2 GB guest RAM, rendered on the host GPU

Each run's emulator costs Windows 5.6-6.9 GB private (measured 2026-11-09): Agent_Phone uses system-images/android-37.0/google_apis_playstore/x86_64, which forces 4096 MB guest RAM over the AVD's hw.ramSize=2048, and tracks/client/track.sh boot() starts it with -gpu swiftshader_indirect (CPU rendering, at 97-100% host CPU during runs). The host has an RTX 4080 Super. The user's word (2026-11-09): BlueStacks felt better than the Android Studio emulator; removing Play services will help. Keep the stock emulator (scripted boot, DNS relay and allowlist, parallel instances by port).
Needed: an AVD on the google_apis (no Play Store) x86_64 image of the same API level, hw.ramSize 2048 honoured, booted with -gpu host; mobile_login's sign-in (Chrome custom tab at Central's form) still works on it, or the browser it needs is installed by the bring-up; the memory wait of h-mobile-login-page-39-again reads the AVD's guest RAM, not a fixed 4096. Privacy unchanged: OPENRUNE=1 LOCAL_AUTH=1 APK, the allowlist and javcheck pass.
Done when: tracks/client/track.sh up <slug> prints LOGGED_IN on 10 consecutive starts on the new AVD, and the evidence records each emulator's Windows private memory and boot-to-LOGGED_IN time against the Play image's (evidence/h-mobile-light-avd/).
