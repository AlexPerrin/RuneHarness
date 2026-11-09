# Client track

RuneLite plugins in the official OSRS Android app (`native/`, `host/`, APK repack) in `~/osrs-plugins-reverse`,
tested on the Agent_Phone emulator against the test server. The script is `tracks/client/track.sh <verb> <slug>`
(verbs in its header); `hd` is the exact command the brief names; the evidence dir is `evidence/<slug>/`. Reference
in the client repo: `docs/app-telemetry.md` (read in full before any build that touches networking),
`docs/plugin-host.md`, `docs/offsets.md`.

## The dev
The brief names your clone (`~/osrs-plugins-reverse/.worktrees/<slug>`, branch `client/<slug>`). Analyse with Ghidra
on `re/ghidra` (`-readOnly` unless the task updates the project); ids and game data from `osrs-mcp`; what the server
sends through `tracks/fork/track.sh log`. `tracks/client/track.sh build <slug>` runs the devtools plugin build, the
host build, ninja and the repack with `OPENRUNE=1 LOCAL_AUTH=1` in the build copy and checks the repack log before
anything is installable; the APK's login modulus is the live stack's key pair's (`state/live/key`), and a cached APK of
another modulus is rebuilt; `up` refuses an APK whose modulus is not the one the live server runs
(`state/live/tree.json`), naming both, before it boots anything; `up <slug>` boots your own emulator on the network
allowlist (checked), maps its 127.0.0.1:8443 and :43594 to the live Central's http and game ports (`adb reverse`: the APK
reads jav_config and signs in at the Central every desktop uses), installs the APK and pushes the devtools jar built with it, logs in and prints the devtools
port; `down` restores and stops it; `log <slug> <pattern>` reads logcat since the run's marker. Test through
`osrs-devtools-mobile` data tools, each call naming `serial` (up's LOGGED_IN line); `adb shell input` only where the emulator refuses injected events. Blocked by the
server: file the blocker as a server change with the repro (`hd new <slug> --track fork --blocks <yours>`); never
work around it. Run the scripted criteria yourself (`check-log`, `check-evidence`, `check-probe`), push
`origin/client/<slug>`, then `hd submit <slug>`.

The mobile side is Windows programs run from bash through WSL interop by absolute path, located by `ANDROID_SDK`
(default `/mnt/c/Users/Alex/AppData/Local/Android/Sdk`: adb.exe, emulator.exe) and `WINDOWS_SYSTEM32` (default
`/mnt/c/Windows/System32`); a missing program fails naming its variable. The emulator runs with no console window,
its log in `state/<slug>/emulator.log`; `down` is the only stop; the emulator's Windows pid and image are recorded
under the run's scope (`state/winpids/`), which `hd stop` ends with the run, and down drops the record. `DOCKER`
(default `docker`) runs the allowlist container `mobile-allow`, one for every mobile, left running. Each mobile asks
DNS of its own relay on Windows (`tracks/client/allow-relay.ps1`, its log `state/<slug>/allow-relay.log`); before
booting, `up` proves `nslookup api.runelite.net <that address>` from Windows gets 10.0.2.2, replacing the container
once when it does not, then fails naming the Windows holders of udp 53.

## The reviewer (releases only)
Full QA on the client's live tip at the exact commit, every finding at once: mobile regression of core and pinned
hub plugins, network QA, sign-in, the privacy patches in the repack log, native claims against Ghidra, the release
notes, the single universal APK (`apksigner verify`, `zipalign -c`, arm64-v8a only, the notices embedded equal to the
committed file), no secrets or personal data. Copy `osrs-runelite.apk`, `THIRD_PARTY_NOTICES.md` and the repack log
into the evidence dir. Releases are `vX.Y.Z`; autonomous builds are 0.1.x; a major version needs the user.

## Network QA (every release, every change with `network: true`)
Sample the app's ESTABLISHED sockets every 0.5 s through the sign-out, LOCAL_AUTH sign-in, play, `::drop` relog and
restart sequence; DNS from logcat's "asked for" lines. Allowed sockets: 127.0.0.1:43594 and :8443 (the game and Central's http: jav_config and the LOCAL_AUTH sign-in, `adb reverse`d by `up` to the live
stack's 43594 and 8084) and 10.0.2.2:443 only. The
network allowlist: `up` starts the container `mobile-allow` (`tracks/client/allow.py`, DNS over tcp 127.0.0.1:8053
and tcp 443) and the emulator with `-dns-server` at its own relay, and turns the mobile's wifi off; the cellular path
asks `mobile-allow`, which answers `api.runelite.net` and `static.runelite.net` with 10.0.2.2 and every other name
NXDOMAIN, and relays a TLS connection on 10.0.2.2:443 to its SNI name only when that name is one of the two. The
Windows Firewall rules of group `osrs-harness` block the emulator's qemu-system-x86_64.exe and netsimd.exe from every
address but loopback and the LAN. `check-blocked` (run by `up`) proves both halves. Must not appear, even as a
lookup: any `jagex.com`, `runescape.com`, `singular.net`, `app-measurement.com`, `*.x.invalid`, ConsentSync or
Singular log lines. First the jav_config the app loads, the live Central's, names local hosts only: `python3
tracks/fork/server/javcheck.py http://127.0.0.1:8084/jav_config.ws` prints `jav_config local only`.
Report as `netqa*.md`.

## Never
Connect anything to Jagex or RuneScape servers (a new outbound host: stop and report at once); restart or edit the
server; touch another agent's mobile or Medium_Phone (it has the official app); read `C:\Users\Alex\.runelite`;
send keyevent BACK in game; push any ref but `client/<slug>`; tag, release or deploy.

## Seed criteria
Scripted criteria run with SLUG, HEAD, T, TCOMMIT, BASE, CLONE, BUILD, EVIDENCE in the env, cwd the build copy.
- repack-log | the repack log has the 7 telemetry lines, patched RSA modulus, patched /jav_config.ws, the appauth line | script: bash $HD_ROOT/tracks/client/track.sh check-log
- mobile-evidence | a logcat extract, dump or devtools JSON in the evidence dir | script: bash $HD_ROOT/tracks/client/track.sh check-evidence
- probe | the probe report is built at HEAD (docs-only differences allowed) | script: bash $HD_ROOT/tracks/client/track.sh check-probe
- network-qa | netqa*.md present and PASS when the change has network: true | script: bash $HD_ROOT/tracks/client/track.sh check-netqa
- state-doc | docs/client-state.md rewritten from the probe report | script: bash $HD_ROOT/tracks/client/track.sh check-state-doc
