---
slug: client-local-auth-debuggable
track: client
priority: P1
upstream: false
---
# the LOCAL_AUTH repack marks the app debuggable: the harness seeds its saved sign-in and accepted terms by run-as

Found by h-mobile-token-login (run 337): the app keeps its sign-in in plain app data, SharedPreferences 'AuthState' (re/jadx/sources/ta/m.java: key 'state', JSON access_Token, token_expires, refresh_Token, identity_Token, identity_token_expires, session_Id), not keystore-bound. Agent_Phone is a google_apis_playstore image (adb root refused), so the harness can write /data/data/com.jagex.oldscape.android only through run-as, which needs android:debuggable="true". Needed: tools/patch_local_auth.py (LOCAL_AUTH=1 only) sets android:debuggable="true" on <application> in the decoded AndroidManifest.xml and prints a 'patched ... debuggable' line in the repack log; nothing else changes (no network effect: OPENRUNE=1 LOCAL_AUTH=1, javcheck and check-log as today). Done when: an up of the built APK answers 'adb shell run-as com.jagex.oldscape.android ls shared_prefs' (after one sign-in it lists AuthState.xml) and the sign-in and Play Now still reach LOGGED_IN. The harness side (Central's session minted for mobile_login.account(), AuthState.xml and the terms written before the one start) is h-mobile-token-login's.

The user's word (2026-11-09): dev builds are debuggable, the official release is not. Debuggable is its own repack switch (not implied by LOCAL_AUTH), set by the agents' build (tracks/client/track.sh build) only; tools/release-dev.sh never sets it and refuses to attach an APK whose manifest is debuggable (aapt dump badging / the decoded manifest), a scripted criterion of this change.
