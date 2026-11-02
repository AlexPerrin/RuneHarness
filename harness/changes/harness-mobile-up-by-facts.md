---
slug: harness-mobile-up-by-facts
track: harness
title: Mobile up does only what the device lacks, each step ended and measured by
  a device fact
kind: change
priority: P1
deps:
- harness-device-network-block
- harness-no-powershell
- client-login-segv-osclient
goal: client-launch
units:
- launch:boot
- launch:files-init
- launch:install
mechanism: mobile
created: '2026-11-01T23:59:47Z'
limit-of:
---
Planner merge (planner-17) of client-launch-measure, client-launch-boot, client-launch-files-init, client-launch-install and harness-mobile-dns-off-loopback. Root cause against PRD's workflow (QA proves a client change on a mobile reached quickly): the mobile up is a fixed script of unconditional steps whose ends are not facts and are never measured: it cold-boots Agent_Phone (-read-only, -gpu swiftshader_indirect) polling sys.boot_completed every 2 s; uninstalls and reinstalls the APK on every up, even for the tree-cached build; starts the app with monkey, sleeps 5 s and force-stops it only so files/ exists; points -dns-server at a Windows loopback address whose udp 53 SharedAccess holds (it cannot be stopped: 'Service Internet Connection Sharing (ICS) (SharedAccess) stop failed.'), so up refuses every mobile; and tools/track.sh measure is the client-api probe only, with no timings (state/log-mark written after login, devtools port hardcoded 7780).

One mechanism replaces those steps: up compares the device's observed state with what the launch needs and does only the difference, each step ending on a device fact, and measure reads those same facts.

Acceptance:
- measure dispatches on GOAL: for client-launch it runs up on a fresh emulator, logs in the tester account on the test server and writes state/client-launch/measure.json {tree, value, report} (value = share of inventory rows in PASSES) and evidence/client-launch/measure.json: per unit, start, end and the fact that ended it, plus the total from logcat 'Start proc' of the app to the first game tick while LOGGED_IN; timestamps only from device records (logcat -v epoch: ActivityTaskManager, PackageManager, osrsrl-host 'host starting'/'host ready'/'httpserver ... port'/GameStateChanged, devtools get_client_state); a step with no readable end is reported so. state/log-mark is written before login and the devtools port read from the httpserver line.
- launch:boot: boot from a saved snapshot per instance (read-only base kept, instances parallel and unlocked), host GPU where offered, boot waited on the device's fact (adb wait-for-device plus a device-side getprop loop or the boot_completed broadcast); the report's boot step is shorter than the measured cold boot; backup and restore on down unchanged.
- launch:install: install -r only when the installed APK's sha256 (pm path + sha256sum) differs from state/build.json's; libosrsrl check and the Chrome local network grant kept; every APK still through the telemetry patch with OPENRUNE=1 LOCAL_AUTH=1; a second up on one tree shows no install step.
- launch:files-init: the plugin and devtools directories created directly (run-as mkdir -p) or waited on as a fact, no throwaway start, no fixed sleep; plugins load at the first real start (logcat 'host ready; N plugin(s) running').
- DNS: -dns-server is an address that is not a Windows loopback SharedAccess holds, on which mobile-allow answers udp 53 for the allowlisted names and refuses the rest, reachable from the Windows emulator; nothing on Windows stopped or reconfigured; up's nslookup proof (expects 10.0.2.2) runs against it; a test covers the address choice.
- Proof: two real measures reaching gameplay, the report's steps in order with their facts. One test per requirement touched.

Also (moved to harness-desktop-one-login-path, which covers every desktop and device): mobile_login.py logs in through the devtools login tool, not taps
client-devtools-login (b7a22bb) gives the devtools plugin a login tool that presses each Android login page's forward button through the client (Native.loginSubmit: Sign in, Accept, Play Now, Try again) and does AppAuth's browser step in-app on local endpoints (LoginAgent), so no Chrome opens. tools/mobile_login.py on client/harness-v8 still taps fixed points (TAPS, LABELS, uiautomator dump, input tap, logcat -d every 3 s). Replace it with evidence/client-devtools-login/mobile_login.py: it streams logcat -v epoch -s osrsrl-host ActivityManager, calls tools/call login over nc once the httpserver token/port line appears, ends on GameStateChanged LOGGED_IN (or the tool's refusal, or the app's death), and prints the client start (Start proc) to LOGGED_IN time on stderr. Needs an APK with client-devtools-login's devtools jar; proved by ten ups ending LOGGED_IN with no tap.
