---
slug: h-mobile-boot-monkey-aborted
track: harness
priority: P1
---
# client up: the first start's monkey aborts on another app's ANR before launching the app, and boot waits on files/ with no end

Run 321, emulator-5560 (Agent_Phone, booted 23:05 local, system_server crashed once in boot 'Lost network stack' and restarted, boot completed in 358 s). track.sh boot(): install OK 23:12:36, check-blocked OK, then 'monkey -p com.jagex.oldscape.android -c android.intent.category.LAUNCHER 1' at 23:13:11 hit 'ANR in com.google.android.gms.persistent' (DOMAINS_NEED_VERIFICATION broadcast) at 23:13:19, and monkey ended 'Events injected: 0' at 23:13:38: the app never started. boot() then loops 'until [ -d files ]' with no end (26 min, focus on the launcher, the app's pid absent, /sdcard/Android/data/<pkg> absent), so up printed nothing past the check-blocked line and mobile_login never ran. Evidence: evidence/h-mobile-signin-no-redirect/stall.logcat.txt (lines 68894-73464), stall-monkey.txt, stall-focus.txt, stall.sockets.txt. Fix on the observed fact: start the app with am start (no ANR abort) or judge monkey's output ('Events injected: 0' / '// NOT RESPONDING') and the app's process, never a wait on files/ alone; the same monkey start in mobile_login.main has the same failure (main waits on the launcher with no end while the app never starts).
