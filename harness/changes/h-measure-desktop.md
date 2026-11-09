---
slug: h-measure-desktop
track: harness
priority: P1
---
# client-api measure: probe on a RuneLite desktop when the mobile login fails

tracks/client/track.sh measure boots the mobile emulator and logs in through the issuer; four starts failed (evidence: state/client-api/measure-*.log: unknown login screens LoginIndex 39 and 3, then the server refusing the login, LoginIndex 9). The user's word: if the mobile keeps failing, try RuneLite. Make measure fall back to a RuneLite desktop instance: when the mobile up fails, bring up one desktop logged into the live test server (the fork track's desktop bring-up in tracks/fork/track.sh, with the live client's devtools-desktop jar that the client build already produces, evidence/<slug>/<T>.devtools-desktop.jar) and run the API probe (tracks/client/api-probe.sh) through its devtools port; record the result with hd measure as the mobile path does, naming the platform in the report. The mobile path stays first. Touch tracks/client (and a shared helper in tracks/fork if the desktop bring-up needs one); add the case to tracks/client/test_track.py.
