---
slug: h-client-up-am-start-default
track: harness
priority: P2
---
# client up never starts the app: am start needs category DEFAULT

Since 3f9853a tracks/client/track.sh up starts the app with 'am start -W -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -p com.jagex.oldscape.android'. am start resolves with MATCH_DEFAULT_ONLY and the app's MainActivity MAIN/LAUNCHER filter has no category.DEFAULT (cmd package query-activities lists it with isDefault=false), so every up ends 'unable to resolve Intent' right after install Success (3 of 3 for client-api-widget-listeners, diag state/client-api-widget-listeners/diag.out). Done when up starts the app by component (-n com.jagex.oldscape.android/com.jagex.android.MainActivity, or am start -W with the resolved launcher) and a client up reaches LOGGED_IN.
